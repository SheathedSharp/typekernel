"""Ink-trap corner filler — triangular/cubic-ish bite into the ink."""

from __future__ import annotations

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import CornerFill, CornerFiller, CornerSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners.geom import clamp_trim, interior_unit, noop_corner_fill, stem_ref
from typekernel.system import System


def _quad_point(a: Point, tip: Point, b: Point, t: float) -> Point:
    omt = 1.0 - t
    return Point(
        omt * omt * a.x + 2.0 * omt * t * tip.x + t * t * b.x,
        omt * omt * a.y + 2.0 * omt * t * tip.y + t * t * b.y,
    )


def ink_trap(
    *,
    size: float = 0.12,
    depth: float | None = None,
    curved: bool = True,
) -> CornerFiller:
    """Return a small bite into the ink (interior), opposite of ``wedge``.

    ``size`` fractions ``stem_ref`` for both trims; ``depth`` fractions
    ``stem_ref`` for how far the tip pushes into the interior (defaults to
    ``size``).

    Path is line segments only (so ``apply_slots`` post-fill G1 checks, which
    skip line–line joins, stay valid). When ``curved`` is true the bite is a
    quadratic polyline through the interior tip; otherwise two lines meet at
    the tip.
    """

    def fill(site: CornerSite, system: System) -> CornerFill:
        stem = stem_ref(site, system)
        raw = max(0.0, float(size) * stem)
        trim_in = clamp_trim(raw, site.in_len)
        trim_out = clamp_trim(raw, site.out_len)
        depth_frac = float(size) if depth is None else float(depth)
        tip_d = max(0.0, depth_frac * stem)
        if trim_in <= 1e-12 and trim_out <= 1e-12:
            return noop_corner_fill(site)

        a = Point(
            site.point.x - site.in_dir.x * trim_in,
            site.point.y - site.in_dir.y * trim_in,
        )
        b = Point(
            site.point.x + site.out_dir.x * trim_out,
            site.point.y + site.out_dir.y * trim_out,
        )
        inn = interior_unit(site)
        tip = Point(site.point.x + inn.x * tip_d, site.point.y + inn.y * tip_d)

        if not curved:
            path = Fragment((LineSegment(a, tip), LineSegment(tip, b)))
            return CornerFill(trim_in=trim_in, trim_out=trim_out, path=path)

        # Quadratic polyline A → … → tip … → B (deterministic segment count).
        samples = 4
        pts = [a]
        for i in range(1, samples):
            pts.append(_quad_point(a, tip, b, i / samples))
        pts.append(b)
        segs = tuple(LineSegment(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        return CornerFill(trim_in=trim_in, trim_out=trim_out, path=Fragment(segs))

    return fill
