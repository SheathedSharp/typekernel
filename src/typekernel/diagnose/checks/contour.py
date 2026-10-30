"""Contour quality diagnostics (S0): node budget, short edges, burrs, slivers, ripple.

Severity uses a coarse visibility model at 16 / 48 / 120 px: a defect that
covers enough design-unit area to light a pixel at any of those sizes becomes
a **warn**; otherwise it stays **info**. This is not a beautifier — it only
reports.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from typekernel.diagnose.protocol import CheckContext, Finding, Scope
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

__all__ = [
    "ContourQualityCheck",
    "defect_visible",
    "visible_px_area",
]

# Soft budgets for structural starters / pen expansion before tidy (S1).
_NODE_BUDGET = 280
_SHORT_DU = 2.0
_BURR_EDGE_DU = 6.0
_BURR_TURN_DEG = 75.0
_SLIVER_AREA_DU = 20.0
_RIPPLE_DOT_THRESH = -0.25


def visible_px_area(size_du: float, render_px: int, upm: float) -> float:
    """Approximate square-pixel area of a ``size_du`` feature at ``render_px``."""
    if upm <= 0:
        return 0.0
    px = abs(size_du) * float(render_px) / float(upm)
    return px * px


def defect_visible(size_du: float, upm: float, *, min_px_area: float = 0.35) -> bool:
    """True when the defect lights ~⅓ px² at 16, 48, or 120 CSS px."""
    for render_px in (16, 48, 120):
        if visible_px_area(size_du, render_px, upm) >= min_px_area:
            return True
    return False


def _seg_length(seg: object) -> float:
    if isinstance(seg, LineSegment):
        a, b = seg.p0, seg.p1
        return math.hypot(b.x - a.x, b.y - a.y)
    if isinstance(seg, CubicSegment):
        # Chord length is enough for short-segment / burr heuristics.
        a, b = seg.p0, seg.p3
        return math.hypot(b.x - a.x, b.y - a.y)
    return 0.0


def _seg_start(seg: object) -> Point:
    if isinstance(seg, LineSegment):
        return seg.p0
    if isinstance(seg, CubicSegment):
        return seg.p0
    raise TypeError(type(seg))


def _seg_end(seg: object) -> Point:
    if isinstance(seg, LineSegment):
        return seg.p1
    if isinstance(seg, CubicSegment):
        return seg.p3
    raise TypeError(type(seg))


def _outdir(a: Point, b: Point) -> tuple[float, float]:
    dx, dy = b.x - a.x, b.y - a.y
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


def _turn_deg(u: tuple[float, float], v: tuple[float, float]) -> float:
    dot = max(-1.0, min(1.0, u[0] * v[0] + u[1] * v[1]))
    return math.degrees(math.acos(dot))


def _poly_area(pts: Sequence[Point]) -> float:
    if len(pts) < 3:
        return 0.0
    acc = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        acc += p.x * q.y - q.x * p.y
    return abs(acc) * 0.5


def _contour_points(segments: Sequence[object]) -> list[Point]:
    pts: list[Point] = []
    for seg in segments:
        pts.append(_seg_start(seg))
    if segments:
        pts.append(_seg_end(segments[-1]))
    return pts


class ContourQualityCheck:
    """Glyph-scope contour hygiene with visibility-aware severity."""

    id = "contour.quality"
    scope: Scope = "glyph"

    def run(self, ctx: CheckContext) -> Iterable[Finding]:
        if ctx.name is None or ctx.final is None:
            return []
        upm = float(ctx.system.upm)
        out: list[Finding] = []
        for ci, contour in enumerate(ctx.final.contours):
            segs = list(contour.segments)
            if not segs:
                continue
            n_nodes = len(segs)
            if n_nodes > _NODE_BUDGET:
                size = float(n_nodes)  # treat excess nodes as defect scale
                level = "warn" if defect_visible(size, upm) else "info"
                out.append(
                    Finding(
                        check="contour.nodes",
                        level=level,  # type: ignore[arg-type]
                        glyph=ctx.name,
                        master=ctx.master,
                        where=f"contour[{ci}]",
                        measured=float(n_nodes),
                        expected=float(_NODE_BUDGET),
                        message=(
                            f"contour[{ci}] has {n_nodes} segments "
                            f"(budget {_NODE_BUDGET}); likely polyline expansion junk"
                        ),
                        hint="reduce sampling or run tidy/refit (S1)",
                    )
                )

            lengths = [_seg_length(s) for s in segs]
            short = [L for L in lengths if 0 < L < _SHORT_DU]
            if short:
                level = "warn" if len(short) >= 50 else "info"
                out.append(
                    Finding(
                        check="contour.short_segment",
                        level=level,  # type: ignore[arg-type]
                        glyph=ctx.name,
                        master=ctx.master,
                        where=f"contour[{ci}]",
                        measured=float(len(short)),
                        expected=0.0,
                        message=(
                            f"contour[{ci}] has {len(short)} segments shorter than "
                            f"{_SHORT_DU} du"
                        ),
                        hint="merge micro-segments / tidy",
                    )
                )

            # Burrs: sharp turn + short adjacent edge.
            burrs = 0
            for i, seg in enumerate(segs):
                nxt = segs[(i + 1) % len(segs)]
                a0, a1 = _seg_start(seg), _seg_end(seg)
                b0, b1 = _seg_start(nxt), _seg_end(nxt)
                u = _outdir(a0, a1)
                v = _outdir(b0, b1)
                turn = _turn_deg(u, v)
                edge = min(_seg_length(seg), _seg_length(nxt))
                if turn >= _BURR_TURN_DEG and edge <= _BURR_EDGE_DU:
                    burrs += 1
            if burrs:
                level = "warn" if burrs >= 80 else "info"
                out.append(
                    Finding(
                        check="contour.burr",
                        level=level,  # type: ignore[arg-type]
                        glyph=ctx.name,
                        master=ctx.master,
                        where=f"contour[{ci}]",
                        measured=float(burrs),
                        expected=0.0,
                        message=f"contour[{ci}] has {burrs} burr-like corners (sharp+short)",
                        hint="smooth terminals; avoid polyline spikes",
                    )
                )

            # Sliver: tiny absolute area relative to stem.
            pts = _contour_points(segs)
            area = _poly_area(pts)
            stem = float(next(iter(ctx.system.stem.values()), 80.0))
            if 0 < area < 5.0:
                level = "info"
                out.append(
                    Finding(
                        check="contour.sliver",
                        level="info",
                        glyph=ctx.name,
                        master=ctx.master,
                        where=f"contour[{ci}]",
                        measured=area,
                        expected=float(stem),
                        message=f"contour[{ci}] looks like a sliver (area={area:.1f} du²)",
                        hint="remove fragment contours from expansion",
                    )
                )

            # Curvature ripple: oscillating cubic handle directions.
            ripples = 0
            prev_dot: float | None = None
            for seg in segs:
                if not isinstance(seg, CubicSegment):
                    continue
                d0 = _outdir(seg.p0, seg.p1)
                d1 = _outdir(seg.p2, seg.p3)
                dot = d0[0] * d1[0] + d0[1] * d1[1]
                if prev_dot is not None and prev_dot < _RIPPLE_DOT_THRESH and dot < _RIPPLE_DOT_THRESH:
                    ripples += 1
                prev_dot = dot
            if ripples:
                # One handle-flip is common on accent marks; sustained oscillation warns.
                level = "warn" if ripples >= 3 or (
                    ripples >= 2 and defect_visible(24.0 * ripples, upm)
                ) else "info"
                out.append(
                    Finding(
                        check="contour.ripple",
                        level=level,  # type: ignore[arg-type]
                        glyph=ctx.name,
                        master=ctx.master,
                        where=f"contour[{ci}]",
                        measured=float(ripples),
                        expected=0.0,
                        message=f"contour[{ci}] shows curvature ripple ({ripples} flips)",
                        hint="refit cubics; avoid high-frequency polyline→curve conversion",
                    )
                )
        return out
