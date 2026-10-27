"""Angled stroke-end filler."""

from __future__ import annotations

import math

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import EndFill, EndFiller, EndSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.ends.geom import cut_len, noop_end_fill, tip_outs
from typekernel.system import System


def angled(*, deg: float = 12.0) -> EndFiller:
    """Return an angled flat terminal (ARCHITECTURE.md example ``angled(deg=12)``).

    Builds a three-segment cap: step out along each tip direction by amounts
    that differ by ``cut_len * tan(deg)``, so the outer edge is sheared by
    ``deg`` degrees relative to the original cut.
    """

    def fill(site: EndSite, system: System) -> EndFill:
        del system
        width = cut_len(site)
        if width <= 1e-12:
            return noop_end_fill(site)
        if abs(float(deg)) <= 1e-12:
            return noop_end_fill(site)
        shear = width * math.tan(math.radians(float(deg)))
        # Mean protrusion = |shear| so both outward steps stay strictly
        # positive when deg != 0 (avoids zero-length stub segments).
        mean = abs(shear)
        s_a = mean + shear * 0.5
        s_b = mean - shear * 0.5
        out_a, out_b = tip_outs(site)
        p1 = Point(site.a.x + out_a.x * s_a, site.a.y + out_a.y * s_a)
        p2 = Point(site.b.x + out_b.x * s_b, site.b.y + out_b.y * s_b)
        path = Fragment(
            (
                LineSegment(site.a, p1),
                LineSegment(p1, p2),
                LineSegment(p2, site.b),
            )
        )
        return EndFill(trim_a=0.0, trim_b=0.0, path=path)

    return fill
