"""Triangular exterior wedge corner filler."""

from __future__ import annotations

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import CornerFill, CornerFiller, CornerSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners.geom import clamp_trim, exterior_unit, stem_ref
from typekernel.system import System


def wedge(*, size: float = 0.25, depth: float | None = None) -> CornerFiller:
    """Return a triangular taper pushed to the exterior.

    ``size`` is a fraction of ``stem_ref`` used for both trims. ``depth`` is the
    exterior tip offset as a fraction of ``stem_ref`` (defaults to ``size``).
    Path: trim point A → exterior tip → trim point B (two lines).
    """

    def fill(site: CornerSite, system: System) -> CornerFill:
        stem = stem_ref(site, system)
        raw = max(0.0, float(size) * stem)
        trim_in = clamp_trim(raw, site.in_len)
        trim_out = clamp_trim(raw, site.out_len)
        depth_frac = float(size) if depth is None else float(depth)
        tip_d = max(0.0, depth_frac * stem)
        if trim_in <= 1e-12 and trim_out <= 1e-12:
            p = site.point
            return CornerFill(0.0, 0.0, Fragment((LineSegment(p, p),)))

        a = Point(
            site.point.x - site.in_dir.x * trim_in,
            site.point.y - site.in_dir.y * trim_in,
        )
        b = Point(
            site.point.x + site.out_dir.x * trim_out,
            site.point.y + site.out_dir.y * trim_out,
        )
        ext = exterior_unit(site)
        tip = Point(site.point.x + ext.x * tip_d, site.point.y + ext.y * tip_d)
        path = Fragment((LineSegment(a, tip), LineSegment(tip, b)))
        return CornerFill(trim_in=trim_in, trim_out=trim_out, path=path)

    return fill
