"""Interpolation checks: mid-instance topology, self-intersection, stem monotonicity."""

from __future__ import annotations

from collections.abc import Iterable

from typekernel.axes.interpolatable import check_drawing_interpolatable
from typekernel.diagnose.protocol import CheckContext, Finding, Scope
from typekernel.draw.drawing import Drawing
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.perceive.topology import measure_topology

__all__ = ["InterpolationCheck", "lerp_drawing", "lerp_outline"]


def _lerp_point(a: Point, b: Point, t: float) -> Point:
    return Point(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)


def lerp_outline(a: Outline, b: Outline, t: float) -> Outline:
    """Linear interpolate two compatible outlines at ``t`` in [0, 1]."""
    if a.contour_count != b.contour_count:
        raise ValueError("contour count mismatch")
    contours: list[Contour] = []
    for ca, cb in zip(a.contours, b.contours, strict=True):
        if len(ca.segments) != len(cb.segments):
            raise ValueError("segment count mismatch")
        segs: list[LineSegment | CubicSegment] = []
        for sa, sb in zip(ca.segments, cb.segments, strict=True):
            if sa.kind != sb.kind:
                raise ValueError("segment kind mismatch")
            pts = tuple(
                _lerp_point(pa, pb, t) for pa, pb in zip(sa.points, sb.points, strict=True)
            )
            if isinstance(sa, LineSegment):
                segs.append(LineSegment(pts[0], pts[1]))
            else:
                segs.append(CubicSegment(pts[0], pts[1], pts[2], pts[3]))
        contours.append(Contour(tuple(segs), closed=ca.closed))
    return Outline(tuple(contours))


def lerp_drawing(a: Drawing, b: Drawing, t: float) -> Drawing:
    """Lerp outlines; keep roles/nodes/slots from ``a`` (structure must match)."""
    if a.signature() != b.signature():
        raise ValueError("drawing signature mismatch")
    outline = lerp_outline(a.outline(), b.outline(), t)
    return Drawing(
        contours=outline.contours,
        roles=a.roles,
        nodes=a.nodes,
        slots=a.slots,
        measures=a.measures,
    )


def _self_intersects(outline: Outline) -> bool:
    """True when pathops.simplify changes contour count (overlap/self-intersect)."""
    try:
        from typekernel.perceive.render import simplify_outline

        simplified = simplify_outline(outline)
    except (ValueError, RuntimeError, TypeError):
        return False
    return simplified.contour_count != outline.contour_count


class InterpolationCheck:
    id = "interpolation"
    scope: Scope = "family"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        project = ctx.project
        session = ctx.session
        masters = list(project.masters)
        if len(masters) < 2:
            return []
        out: list[Finding] = []
        # Pick a weight-ordered pair when locations have wght.
        def wght(m: object) -> float:
            loc = getattr(m, "location", {})
            return float(loc.get("wght", 0.0))

        ordered = sorted(masters, key=wght)
        light, bold = ordered[0], ordered[-1]

        for name in session.specs():
            try:
                d0 = session.evaluate(name, master=light.name).drawing
                d1 = session.evaluate(name, master=bold.name).drawing
            except (KeyError, ValueError, TypeError, RuntimeError):
                continue
            problems = check_drawing_interpolatable([d0, d1])
            for msg in problems:
                out.append(
                    Finding(
                        check="interpolation.compat",
                        level="warn",
                        glyph=name,
                        master=f"{light.name}/{bold.name}",
                        where=None,
                        measured=None,
                        expected=None,
                        message=msg,
                        hint="match contour/segment structure across masters",
                    )
                )
            if problems:
                continue
            stem0 = float(light.system.stem.get("lc", 80.0))
            stem1 = float(bold.system.stem.get("lc", 80.0))
            prev_stem = stem0
            for t in (0.25, 0.5, 0.75):
                try:
                    mid = lerp_drawing(d0, d1, t)
                except ValueError as exc:
                    out.append(
                        Finding(
                            check="interpolation.lerp",
                            level="warn",
                            glyph=name,
                            master=f"t={t}",
                            where=None,
                            measured=None,
                            expected=None,
                            message=str(exc),
                        )
                    )
                    continue
                # Overlap-built masters (stem+bowl) also simplify to fewer
                # contours; only warn when mid introduces intersection the
                # endpoint masters do not already share.
                mid_si = _self_intersects(mid.outline())
                if mid_si and not (
                    _self_intersects(d0.outline()) or _self_intersects(d1.outline())
                ):
                    out.append(
                        Finding(
                            check="interpolation.self_intersect",
                            level="warn",
                            glyph=name,
                            master=f"t={t}",
                            where=None,
                            measured=t,
                            expected=None,
                            message=f"interpolated instance at t={t} self-intersects",
                            hint="fix start-point / contour order between masters",
                        )
                    )
                # Topology at mid should match masters when Light/Bold agree.
                # Overlap joins can change slit-counter counts at endpoints
                # already; only flag mid regressions vs a shared master topo.
                topo0 = measure_topology(d0.outline(), stem=stem0)
                topo1 = measure_topology(d1.outline(), stem=stem1)
                topo_t = measure_topology(mid.outline(), stem=stem0 + (stem1 - stem0) * t)
                masters_agree = (
                    topo0.counters == topo1.counters
                    and topo0.islands == topo1.islands
                )
                if masters_agree and (
                    topo_t.counters != topo0.counters
                    or topo_t.islands != topo0.islands
                ):
                    out.append(
                        Finding(
                            check="interpolation.topology",
                            level="warn",
                            glyph=name,
                            master=f"t={t}",
                            where=None,
                            measured=f"c={topo_t.counters},i={topo_t.islands}",
                            expected=f"c={topo0.counters},i={topo0.islands}",
                            message=(
                                f"topology at t={t} differs from light master"
                            ),
                        )
                    )
                # Stem monotonic along wght (system stem targets).
                stem_t = stem0 + (stem1 - stem0) * t
                if stem_t + 1e-6 < prev_stem:
                    out.append(
                        Finding(
                            check="interpolation.stem_mono",
                            level="warn",
                            glyph=name,
                            master=f"t={t}",
                            where=None,
                            measured=stem_t,
                            expected=f">={prev_stem}",
                            message="stem target not monotonic along wght",
                        )
                    )
                prev_stem = stem_t
        return out
