"""Rectangular slab serif corner filler."""

from __future__ import annotations

from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import CornerFill, CornerFiller, CornerSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners.geom import clamp_trim, exterior_unit, noop_corner_fill, stem_ref
from typekernel.system import System


def slab(*, length: float = 0.42, thickness: float = 0.18) -> CornerFiller:
    """Return a rectangular exterior slab filler.

    ``length`` and ``thickness`` are fractions of the stem reference width
    (``site.meta['stem']``, else a ``System.stem`` entry, else
    ``min(in_len, out_len)``).

    Geometry (synthetic, no letter names):

    - ``trim_in = length * stem`` along the incoming edge
    - ``trim_out = thickness * stem`` along the outgoing edge
    - path is a three-segment parallelogram bump pushed to the **exterior**
      by ``thickness * stem`` along the exterior unit normal (right of travel
      for a CCW turn, left otherwise)

    This matches the ARCHITECTURE.md example
    ``slab(length=0.42, thickness=0.18)``.
    """

    def fill(site: CornerSite, system: System) -> CornerFill:
        stem = stem_ref(site, system)
        raw_in = max(0.0, float(length) * stem)
        raw_out = max(0.0, float(thickness) * stem)
        depth = max(0.0, float(thickness) * stem)
        # Opposite corners share each edge; need headroom on both sides or the
        # next fill collapses a side to zero length (ContinuityError).
        need = max(raw_in, raw_out) * 2.05
        if site.in_len < need or site.out_len < need:
            return noop_corner_fill(site)
        trim_in = clamp_trim(raw_in, site.in_len)
        trim_out = clamp_trim(raw_out, site.out_len)
        # Keep depth from collapsing the parallelogram when trims clamp hard.
        depth = min(depth, max(trim_in, trim_out, 0.0))
        if trim_in <= 1e-12 and trim_out <= 1e-12:
            return noop_corner_fill(site)

        a = site.point_in(trim_in)
        b = site.point_out(trim_out)
        ext = exterior_unit(site)
        p1 = Point(a.x + ext.x * depth, a.y + ext.y * depth)
        p2 = Point(b.x + ext.x * depth, b.y + ext.y * depth)
        path = Fragment(
            (
                LineSegment(a, p1),
                LineSegment(p1, p2),
                LineSegment(p2, b),
            )
        )
        return CornerFill(trim_in=trim_in, trim_out=trim_out, path=path)

    fill.requires = frozenset({"line-line"})  # type: ignore[attr-defined]
    return fill
