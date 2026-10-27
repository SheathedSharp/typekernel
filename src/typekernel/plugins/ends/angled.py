"""Angled stroke-end filler."""

from __future__ import annotations

import math

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import EndFill, EndFiller, EndSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.ends.geom import cut_len, tip_outs
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
            return EndFill(0.0, 0.0, Fragment((LineSegment(site.a, site.b),)))
        shear = width * math.tan(math.radians(float(deg)))
        # Mean protrusion keeps the tip roughly centered; shear tilts it.
        base = abs(shear) * 0.5
        s_a = base + shear * 0.5
        s_b = base - shear * 0.5
        # Ensure non-negative outward steps (flip sense if needed).
        if s_a < 0.0 or s_b < 0.0:
            shift = min(s_a, s_b)
            s_a -= shift
            s_b -= shift
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
