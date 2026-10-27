"""Letter-free geometric constructors (ARCHITECTURE.md §9.6)."""

from __future__ import annotations

import math
from typing import Literal, TypeAlias, cast

from typekernel.draw.fragment import Fragment
from typekernel.geo.curves import quarter_superellipse_cubics, tensioned_cubic
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

PointLike: TypeAlias = Point | tuple[float, float]


def _as_point(p: PointLike) -> Point:
    if isinstance(p, Point):
        return p
    return Point(float(p[0]), float(p[1]))


def _unit(v: Point) -> Point:
    length = math.hypot(v.x, v.y)
    if length < 1e-12:
        raise ValueError("zero-length direction")
    return Point(v.x / length, v.y / length)


def tensioned_arc(
    p0: PointLike,
    t0: PointLike,
    p1: PointLike,
    t1: PointLike,
    *,
    tension: float = 0.55,
) -> Fragment:
    """Single cubic from ``p0`` along ``t0`` arriving along ``t1`` at ``p1``.

    ``tension`` is handle-length / chord-length (ARCHITECTURE.md §9.6).
    """
    a = _as_point(p0)
    b = _as_point(p1)
    seg = tensioned_cubic(
        a,
        b,
        _as_point(t0),
        _as_point(t1),
        tension=1.0,
        bias=0.0,
        handle_ratio=tension,
    )
    return Fragment((seg,))


def superellipse_quarter(
    center: PointLike,
    rx: float,
    ry: float,
    quadrant: int,
    *,
    exponent: float,
) -> Fragment:
    """One CCW superellipse quadrant as a Fragment (via geo.curves)."""
    if quadrant not in (0, 1, 2, 3):
        raise ValueError(f"quadrant must be 0..3, got {quadrant!r}")
    c = _as_point(center)
    p0, p1, p2, p3 = quarter_superellipse_cubics(
        c.x, c.y, rx, ry, cast(Literal[0, 1, 2, 3], quadrant), n=exponent
    )
    return Fragment((CubicSegment(p0, p1, p2, p3),))


def spring(
    stem_edge_x: float,
    y_from: float,
    y_to: float,
    toward: PointLike,
    *,
    depth: float,
    tension: float,
) -> Fragment:
    """G1 transition from a vertical stem edge into a curve toward ``toward``.

    Starts at ``(stem_edge_x, y_from)`` with vertical tangent toward ``y_to``,
    ends at a point inset by ``depth`` toward ``toward`` from the stem edge at
    ``y_to``, with tangent aimed at ``toward``.
    """
    if depth < 0:
        raise ValueError(f"depth must be >= 0, got {depth!r}")
    tgt = _as_point(toward)
    p0 = Point(stem_edge_x, y_from)
    # Vertical direction along the stem edge
    dy = y_to - y_from
    if abs(dy) < 1e-12:
        raise ValueError("y_from and y_to must differ")
    t0 = Point(0.0, 1.0 if dy > 0 else -1.0)
    # End sits ``depth`` from the stem toward the target (horizontal component)
    side = 1.0 if tgt.x >= stem_edge_x else -1.0
    p1 = Point(stem_edge_x + side * depth, y_to)
    t1 = _unit(Point(tgt.x - p1.x, tgt.y - p1.y))
    return tensioned_arc(p0, t0, p1, t1, tension=tension)



def hook(
    stem_edge_x: float,
    y_join: float,
    tip: PointLike,
    *,
    depth: float,
    tension: float = 0.55,
    tip_tangent: PointLike | None = None,
) -> Fragment:
    """G1 hook from a vertical stem edge to ``tip`` (ARCHITECTURE.md §9.6).

    Leaves ``(stem_edge_x, y_join)`` with a vertical tangent toward ``tip.y``,
    passes through a belly at horizontal offset ``depth`` (same side as the tip),
    and arrives at ``tip``. Default tip tangent is horizontal back toward the
    stem (curl). Built as two ``tensioned_arc`` cubics meeting G1 at the belly.
    """
    if depth < 0:
        raise ValueError(f"depth must be >= 0, got {depth!r}")
    tip_p = _as_point(tip)
    p0 = Point(stem_edge_x, y_join)
    dy = tip_p.y - y_join
    if abs(dy) < 1e-12:
        raise ValueError("tip.y must differ from y_join for a vertical-stem hook")
    t0 = Point(0.0, 1.0 if dy > 0 else -1.0)
    side = 1.0 if tip_p.x >= stem_edge_x else -1.0
    if tip_tangent is None:
        t1 = Point(-side, 0.0)
    else:
        t1 = _unit(_as_point(tip_tangent))
    belly = Point(stem_edge_x + side * depth, (y_join + tip_p.y) * 0.5)
    # Horizontal tangent at belly keeps both cubics G1 (same in/out direction).
    t_belly = Point(side, 0.0)
    first = tensioned_arc(p0, t0, belly, t_belly, tension=tension)
    second = tensioned_arc(belly, t_belly, tip_p, t1, tension=tension)
    return Fragment(first.segments + second.segments)

def diagonal_band(
    p_top: PointLike,
    p_bottom: PointLike,
    *,
    weight: float,
    compensate: bool = True,
) -> tuple[Fragment, Fragment]:
    """Two edges of a diagonal stroke with visual ``weight``.

    When ``compensate`` is true, the perpendicular distance between the edges
    equals ``weight`` (angle-corrected); otherwise ``weight`` is the horizontal
    offset magnitude.
    """
    if weight <= 0:
        raise ValueError(f"weight must be positive, got {weight!r}")
    top = _as_point(p_top)
    bottom = _as_point(p_bottom)
    dx = bottom.x - top.x
    dy = bottom.y - top.y
    length = math.hypot(dx, dy)
    if length < 1e-12:
        raise ValueError("p_top and p_bottom must differ")
    # Unit along stroke (top → bottom) and left-hand normal
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux
    if compensate:
        # Perpendicular half-offset so full width == weight
        half = weight / 2.0
    else:
        # Treat weight as horizontal separation; convert via |nx| component
        if abs(nx) < 1e-12:
            half = weight / 2.0
        else:
            half = (weight / 2.0) / abs(nx)
    left_top = Point(top.x + nx * half, top.y + ny * half)
    left_bot = Point(bottom.x + nx * half, bottom.y + ny * half)
    right_top = Point(top.x - nx * half, top.y - ny * half)
    right_bot = Point(bottom.x - nx * half, bottom.y - ny * half)
    left = Fragment((LineSegment(left_top, left_bot),))
    right = Fragment((LineSegment(right_bot, right_top),))  # opposite direction
    return left, right
