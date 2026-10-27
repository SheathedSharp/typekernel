"""Flat stroke-end filler."""

from __future__ import annotations

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import EndFill, EndFiller, EndSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.ends.geom import cut_len, stem_ref, tip_outs
from typekernel.system import System


def flat(*, inset: float = 0.0) -> EndFiller:
    """Return a flat terminal filler.

    ``inset`` is a fraction of ``stem_ref``: when zero, the cut is kept as a
    straight ``Line(a, b)``. When positive, the path steps out along each tip
    direction by ``inset * stem`` then across, forming a shallow flat cap.
    """

    def fill(site: EndSite, system: System) -> EndFill:
        depth = max(0.0, float(inset) * stem_ref(site, system))
        if depth <= 1e-12 or cut_len(site) <= 1e-12:
            path = Fragment((LineSegment(site.a, site.b),))
            return EndFill(trim_a=0.0, trim_b=0.0, path=path)
        out_a, out_b = tip_outs(site)
        p1 = Point(site.a.x + out_a.x * depth, site.a.y + out_a.y * depth)
        p2 = Point(site.b.x + out_b.x * depth, site.b.y + out_b.y * depth)
        path = Fragment(
            (
                LineSegment(site.a, p1),
                LineSegment(p1, p2),
                LineSegment(p2, site.b),
            )
        )
        return EndFill(trim_a=0.0, trim_b=0.0, path=path)

    return fill
