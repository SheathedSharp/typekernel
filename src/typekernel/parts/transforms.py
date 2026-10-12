"""Affine transforms on cubic outlines (Three.js Object3D-style moves).

Agents compose letters by placing parts in a shared design space: translate to
position a stem, scale a bowl, rotate a diagonal. Transforms keep cubic handles
and never flatten curves.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment


def translate(outline: Outline, dx: float, dy: float = 0.0) -> Outline:
    """Shift every control point by ``(dx, dy)``."""
    return _map_points(outline, lambda p: Point(p.x + dx, p.y + dy))


def scale(
    outline: Outline,
    sx: float,
    sy: float | None = None,
    *,
    origin: tuple[float, float] = (0.0, 0.0),
) -> Outline:
    """Scale about ``origin``. ``sy`` defaults to ``sx`` (uniform)."""
    if sy is None:
        sy = sx
    ox, oy = origin

    def map_pt(p: Point) -> Point:
        return Point(ox + (p.x - ox) * sx, oy + (p.y - oy) * sy)

    return _map_points(outline, map_pt)


def rotate(
    outline: Outline,
    degrees: float,
    *,
    origin: tuple[float, float] = (0.0, 0.0),
) -> Outline:
    """Rotate counter-clockwise about ``origin`` by ``degrees``."""
    rad = math.radians(degrees)
    c, s = math.cos(rad), math.sin(rad)
    ox, oy = origin

    def map_pt(p: Point) -> Point:
        x, y = p.x - ox, p.y - oy
        return Point(ox + x * c - y * s, oy + x * s + y * c)

    return _map_points(outline, map_pt)


def mirror_x(outline: Outline, *, at_x: float = 0.0) -> Outline:
    """Reflect across the vertical line ``x = at_x``."""
    return _map_points(outline, lambda p: Point(2.0 * at_x - p.x, p.y))


def mirror_y(outline: Outline, *, at_y: float = 0.0) -> Outline:
    """Reflect across the horizontal line ``y = at_y``."""
    return _map_points(outline, lambda p: Point(p.x, 2.0 * at_y - p.y))


def _map_points(outline: Outline, mapper: Callable[[Point], Point]) -> Outline:
    contours: list[Contour] = []
    for c in outline.contours:
        segs: list[LineSegment | CubicSegment] = []
        for seg in c.segments:
            pts = [mapper(p) for p in seg.points]
            if isinstance(seg, LineSegment):
                segs.append(LineSegment(pts[0], pts[1]))
            else:
                segs.append(CubicSegment(*pts))
        contours.append(Contour(tuple(segs), closed=c.closed))
    return Outline(tuple(contours))
