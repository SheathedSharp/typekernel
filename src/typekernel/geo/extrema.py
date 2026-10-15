"""Axis-aligned extrema on cubics (TK-402 italic curve rebalance)."""

from __future__ import annotations

import math

from fontTools.misc.bezierTools import splitCubicAtT

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

__all__ = ["outline_with_axis_extrema_on_curve"]

_EPS = 1e-9
_MIN_INTERIOR_T = 1e-5


def _quad_roots_open_unit(a: float, b: float, c: float) -> list[float]:
    if abs(a) < _EPS:
        if abs(b) < _EPS:
            return []
        t = -c / b
        return [t] if _MIN_INTERIOR_T < t < 1.0 - _MIN_INTERIOR_T else []
    disc = b * b - 4.0 * a * c
    if disc < 0:
        return []
    if disc == 0:
        t = -b / (2.0 * a)
        return [t] if _MIN_INTERIOR_T < t < 1.0 - _MIN_INTERIOR_T else []
    s = math.sqrt(disc)
    out: list[float] = []
    for t in ((-b - s) / (2.0 * a), (-b + s) / (2.0 * a)):
        if _MIN_INTERIOR_T < t < 1.0 - _MIN_INTERIOR_T:
            out.append(t)
    return out


def _cubic_axis_extrema_ts(seg: CubicSegment) -> list[float]:
    p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
    c0x, c0y = 3.0 * (p1.x - p0.x), 3.0 * (p1.y - p0.y)
    c1x, c1y = 6.0 * (p2.x - p1.x), 6.0 * (p2.y - p1.y)
    c2x, c2y = 3.0 * (p3.x - p2.x), 3.0 * (p3.y - p2.y)
    ax, bx, cx = c0x - c1x + c2x, -2.0 * c0x + c1x, c0x
    ay, by, cy = c0y - c1y + c2y, -2.0 * c0y + c1y, c0y
    ts = set(_quad_roots_open_unit(ax, bx, cx))
    ts.update(_quad_roots_open_unit(ay, by, cy))
    return sorted(ts)


def _split_cubic_at_ts(seg: CubicSegment, ts: list[float]) -> tuple[CubicSegment | LineSegment, ...]:
    if not ts:
        return (seg,)
    parts: list[CubicSegment | LineSegment] = []
    current = seg
    for t in ts:
        pts = [p.as_tuple() for p in current.points]
        left, right = splitCubicAtT(*pts, t)
        parts.append(CubicSegment(*(Point(*p) for p in left)))
        current = CubicSegment(*(Point(*p) for p in right))
    parts.append(current)
    return tuple(parts)


def _contour_with_axis_extrema(contour: Contour) -> Contour:
    new_segs: list[LineSegment | CubicSegment] = []
    for seg in contour.segments:
        if isinstance(seg, LineSegment):
            new_segs.append(seg)
            continue
        ts = _cubic_axis_extrema_ts(seg)
        new_segs.extend(_split_cubic_at_ts(seg, ts))
    return Contour(tuple(new_segs), closed=contour.closed)


def outline_with_axis_extrema_on_curve(outline: Outline) -> Outline:
    """Split cubics so horizontal/vertical turning points land on on-curve nodes."""
    return Outline(tuple(_contour_with_axis_extrema(ct) for ct in outline.contours))
