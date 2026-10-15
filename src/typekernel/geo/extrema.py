"""Axis-aligned extrema on cubics (TK-402 italic curve rebalance)."""

from __future__ import annotations

import math

from fontTools.misc.bezierTools import splitCubicAtT

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

__all__ = [
    "cubic_has_off_node_axis_extrema",
    "oblique_compat_split_ts",
    "outline_e_oblique_splits",
    "outline_oblique_compat_splits",
    "outline_with_axis_extrema_on_curve",
]

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


def _cubic_at(seg: CubicSegment, t: float) -> Point:
    u = 1.0 - t
    p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
    return Point(
        u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x,
        u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y,
    )


def cubic_has_off_node_axis_extrema(
    seg: CubicSegment,
    *,
    endpoint_tol: float = 0.5,
) -> bool:
    """True when an axis-aligned turning point is not near ``p0`` or ``p3``."""
    p0, p3 = seg.p0, seg.p3
    chord = math.hypot(p3.x - p0.x, p3.y - p0.y)
    tol = max(endpoint_tol, chord * 0.02)
    for t in _cubic_axis_extrema_ts(seg):
        pt = _cubic_at(seg, t)
        d0 = math.hypot(pt.x - p0.x, pt.y - p0.y)
        d3 = math.hypot(pt.x - p3.x, pt.y - p3.y)
        if min(d0, d3) > tol:
            return True
    return False


def _cubic_deriv_quad_coeffs(
    seg: CubicSegment,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
    c0x, c0y = 3.0 * (p1.x - p0.x), 3.0 * (p1.y - p0.y)
    c1x, c1y = 6.0 * (p2.x - p1.x), 6.0 * (p2.y - p1.y)
    c2x, c2y = 3.0 * (p3.x - p2.x), 3.0 * (p3.y - p2.y)
    ax, bx, cx = c0x - c1x + c2x, -2.0 * c0x + c1x, c0x
    ay, by, cy = c0y - c1y + c2y, -2.0 * c0y + c1y, c0y
    return (ax, bx, cx), (ay, by, cy)


def oblique_compat_split_ts(seg: CubicSegment, shear: float) -> list[float]:
    """Parameters to split *before* shear so oblique axis extrema sit on nodes."""
    (ax, bx, cx), (ay, by, cy) = _cubic_deriv_quad_coeffs(seg)
    ts = set(_quad_roots_open_unit(ay, by, cy))
    sx, sy, sz = ax + shear * ay, bx + shear * by, cx + shear * cy
    ts.update(_quad_roots_open_unit(sx, sy, sz))
    return sorted(ts)


def _cubic_axis_extrema_ts(seg: CubicSegment) -> list[float]:
    (ax, bx, cx), (ay, by, cy) = _cubic_deriv_quad_coeffs(seg)
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


def _contour_oblique_compat_splits(contour: Contour, shear: float) -> Contour:
    new_segs: list[LineSegment | CubicSegment] = []
    for seg in contour.segments:
        if isinstance(seg, LineSegment):
            new_segs.append(seg)
            continue
        ts = oblique_compat_split_ts(seg, shear)
        new_segs.extend(_split_cubic_at_ts(seg, ts))
    return Contour(tuple(new_segs), closed=contour.closed)


def outline_oblique_compat_splits(outline: Outline, shear: float) -> Outline:
    """Split cubics for a later horizontal shear (TK-402, VF-safe)."""
    if abs(shear) < 1e-12:
        return outline
    return Outline(tuple(_contour_oblique_compat_splits(ct, shear) for ct in outline.contours))


_E_EYE_FALLBACK_SPLIT_T = 0.94


def _e_eye_oblique_segment_parity(eye: Contour) -> Contour:
    """Heavy ``e`` eyes may miss an oblique split; match the regular eye topology."""
    if len(eye.segments) != 3:
        return eye
    seg = eye.segments[2]
    if not isinstance(seg, CubicSegment):
        return eye
    new_segs: list[LineSegment | CubicSegment] = list(eye.segments[:2])
    new_segs.extend(_split_cubic_at_ts(seg, [_E_EYE_FALLBACK_SPLIT_T]))
    return Contour(tuple(new_segs), closed=eye.closed)


def outline_e_oblique_splits(outline: Outline, shear: float) -> Outline:
    """Oblique pre-splits for ``e``; normalises eye contour segment counts (TK-402)."""
    split = outline_oblique_compat_splits(outline, shear)
    if len(split.contours) < 2:
        return split
    outer, eye = split.contours[0], split.contours[1]
    eye = _e_eye_oblique_segment_parity(eye)
    return Outline((outer, eye))


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
