"""Rounded (fillet) corner filler via a single circular-ish cubic."""

from __future__ import annotations

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import CornerFill, CornerFiller, CornerSite
from typekernel.geo.path_helpers import KAPPA
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment
from typekernel.plugins.corners.geom import clamp_trim, noop_corner_fill, stem_ref
from typekernel.system import System


def rounded(*, radius: float | None = None) -> CornerFiller:
    """Return a circular fillet filler.

    ``radius`` is design units. When omitted, uses ``site.meta['radius']``, else
    half of ``stem_ref`` (meta stem / System.stem / min edge length). The radius
    is clamped to half of each adjacent edge so trims stay on-segment.
    """

    def fill(site: CornerSite, system: System) -> CornerFill:
        if radius is not None:
            r_req = float(radius)
        elif "radius" in site.meta:
            r_req = float(site.meta["radius"])
        else:
            r_req = 0.5 * stem_ref(site, system)
        r_req = max(r_req, 0.0)
        r = min(r_req, site.in_len * 0.5, site.out_len * 0.5)
        r = clamp_trim(r, min(site.in_len, site.out_len))
        if r <= 1e-12:
            return noop_corner_fill(site)

        start = Point(
            site.point.x - site.in_dir.x * r,
            site.point.y - site.in_dir.y * r,
        )
        end = Point(
            site.point.x + site.out_dir.x * r,
            site.point.y + site.out_dir.y * r,
        )
        c1 = Point(
            start.x + site.in_dir.x * r * KAPPA,
            start.y + site.in_dir.y * r * KAPPA,
        )
        c2 = Point(
            end.x - site.out_dir.x * r * KAPPA,
            end.y - site.out_dir.y * r * KAPPA,
        )
        return CornerFill(
            trim_in=r,
            trim_out=r,
            path=Fragment((CubicSegment(start, c1, c2, end),)),
        )

    return fill
