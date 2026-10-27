"""Ball (bulb) stroke-end filler."""

from __future__ import annotations

import math

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import EndFill, EndFiller, EndSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.ends.geom import cut_len, tip_outs, unit
from typekernel.system import System


def ball(*, radius: float | None = None, samples: int = 8) -> EndFiller:
    """Return a bulb terminal approximated by a semicircle polyline.

    ``radius`` is design units; default is half the cut length. Uses line
    segments only so stem↔path corners stay line–line (exempt from the
    post-fill G1 check) while still forming a round tip.
    """

    def fill(site: EndSite, system: System) -> EndFill:
        del system
        width = cut_len(site)
        if width <= 1e-12:
            return EndFill(0.0, 0.0, Fragment((LineSegment(site.a, site.b),)))
        r = float(radius) if radius is not None else 0.5 * width
        r = max(0.0, r)
        if r <= 1e-12:
            return EndFill(0.0, 0.0, Fragment((LineSegment(site.a, site.b),)))
        out_a, out_b = tip_outs(site)
        out = unit(Point(out_a.x + out_b.x, out_a.y + out_b.y))
        if abs(out.x) < 1e-12 and abs(out.y) < 1e-12:
            out = out_a
        across = unit(Point(site.b.x - site.a.x, site.b.y - site.a.y))
        mid = Point(0.5 * (site.a.x + site.b.x), 0.5 * (site.a.y + site.b.y))
        # Semicircle in the plane spanned by ``across`` and ``out``, centered
        # at ``mid``, from a to b through mid+out*r.
        n = max(4, int(samples))
        pts: list[Point] = [site.a]
        for i in range(1, n):
            ang = math.pi * (i / n)  # 0→π
            # At 0: -across direction from mid toward a; at π: +across toward b.
            # a ≈ mid - across*(width/2), b ≈ mid + across*(width/2).
            half = width * 0.5
            rx = half  # along across
            ry = r  # along out
            # Angle from a-side (π) to b-side (0) through out (π/2):
            theta = math.pi - ang
            p = Point(
                mid.x + math.cos(theta) * rx * across.x + math.sin(theta) * ry * out.x,
                mid.y + math.cos(theta) * rx * across.y + math.sin(theta) * ry * out.y,
            )
            pts.append(p)
        pts.append(site.b)
        segs = tuple(LineSegment(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
        return EndFill(trim_a=0.0, trim_b=0.0, path=Fragment(segs))

    return fill
