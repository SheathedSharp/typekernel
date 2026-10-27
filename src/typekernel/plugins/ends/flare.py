"""Flared stroke-end filler."""

from __future__ import annotations

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import EndFill, EndFiller, EndSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.ends.geom import cut_len, noop_end_fill, stem_ref, tip_outs, unit
from typekernel.system import System


def flare(*, amount: float = 0.35, depth: float = 0.25) -> EndFiller:
    """Return a trapezoid flare past the cut.

    ``amount`` and ``depth`` are fractions of ``stem_ref``. The path widens
    past each cut endpoint by ``amount * stem`` along the cut axis, then
    steps out ``depth * stem`` along the tip directions.
    """

    def fill(site: EndSite, system: System) -> EndFill:
        width = cut_len(site)
        if width <= 1e-12:
            return noop_end_fill(site)
        stem = stem_ref(site, system)
        extra = max(0.0, float(amount) * stem)
        dep = max(0.0, float(depth) * stem)
        if extra <= 1e-12 and dep <= 1e-12:
            return noop_end_fill(site)
        across = unit(Point(site.b.x - site.a.x, site.b.y - site.a.y))
        out_a, out_b = tip_outs(site)
        # Widen outward from a (opposite across) and from b (along across).
        wa = Point(site.a.x - across.x * extra, site.a.y - across.y * extra)
        wb = Point(site.b.x + across.x * extra, site.b.y + across.y * extra)
        p1 = Point(wa.x + out_a.x * dep, wa.y + out_a.y * dep)
        p2 = Point(wb.x + out_b.x * dep, wb.y + out_b.y * dep)
        path = Fragment(
            (
                LineSegment(site.a, wa),
                LineSegment(wa, p1),
                LineSegment(p1, p2),
                LineSegment(p2, wb),
                LineSegment(wb, site.b),
            )
        )
        return EndFill(trim_a=0.0, trim_b=0.0, path=path)

    return fill
