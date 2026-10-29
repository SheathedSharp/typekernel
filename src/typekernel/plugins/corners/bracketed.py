"""Bracketed serif: slab rectangle plus a concave cubic into the stem."""

from __future__ import annotations

from typekernel.draw.construct import tensioned_arc
from typekernel.draw.fragment import Fragment
from typekernel.draw.slots import CornerFill, CornerFiller, CornerSite
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners.geom import (
    clamp_trim,
    exterior_unit,
    noop_corner_fill,
    stem_ref,
    unit,
)
from typekernel.system import System


def bracketed(
    *,
    length: float = 0.42,
    thickness: float = 0.18,
    tension: float = 0.55,
) -> CornerFiller:
    """Return a slab-like filler with a concave bracket into the outgoing edge.

    ``length`` / ``thickness`` are fractions of ``stem_ref`` (same rule as
    ``slab``). The path is ``A → P1 → P2`` (exterior parallelogram edges) then
    a ``tensioned_arc`` from ``P2`` into ``B`` on the stem so the join is a
    soft concave bracket rather than a sharp outer corner at the stem.
    """

    def fill(site: CornerSite, system: System) -> CornerFill:
        stem = stem_ref(site, system)
        raw_in = max(0.0, float(length) * stem)
        raw_out = max(0.0, float(thickness) * stem)
        depth = max(0.0, float(thickness) * stem)
        trim_in = clamp_trim(raw_in, site.in_len)
        trim_out = clamp_trim(raw_out, site.out_len)
        depth = min(depth, max(trim_in, trim_out, 0.0))
        if trim_in <= 1e-12 and trim_out <= 1e-12:
            return noop_corner_fill(site)

        a = site.point_in(trim_in)
        b = site.point_out(trim_out)
        ext = exterior_unit(site)
        p1 = Point(a.x + ext.x * depth, a.y + ext.y * depth)
        p2 = Point(b.x + ext.x * depth, b.y + ext.y * depth)

        along = Point(p2.x - p1.x, p2.y - p1.y)
        if abs(along.x) < 1e-12 and abs(along.y) < 1e-12:
            # Degenerate outer edge: fall back to sharp slab lines.
            path = Fragment(
                (LineSegment(a, p1), LineSegment(p1, p2), LineSegment(p2, b))
            )
            return CornerFill(trim_in=trim_in, trim_out=trim_out, path=path)

        # Bracket cubic: leave along the outer edge, arrive along out_dir.
        bracket = tensioned_arc(p2, unit(along), b, site.out_dir, tension=float(tension))
        path = Fragment((LineSegment(a, p1), LineSegment(p1, p2), *bracket.segments))
        return CornerFill(trim_in=trim_in, trim_out=trim_out, path=path)

    fill.requires = frozenset({"line-line"})  # type: ignore[attr-defined]
    return fill
