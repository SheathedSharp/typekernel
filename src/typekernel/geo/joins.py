"""Curvature-aware join blending for outlines.

Replaces "boolean union + fillet pad" patching with an explicit operator:
every selected corner is trimmed back along both neighbours and bridged by
one cubic whose two handles meet at the tangent intersection. Against
straight neighbours that cubic is **G2** (zero curvature at both ends, so no
curvature jump); against curved neighbours it is at least **G1**.

Agent-facing entry points:

- :func:`join_angles` / :func:`classify_joins` — read what a contour has
- :func:`blend_corners` — smooth chosen corners (crotches, kinks, shoulders)
- :func:`curvature_jump` — G2 diagnostic at already-smooth joins
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from fontTools.misc.bezierTools import splitCubicAtT

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.smoothness import incoming_tangent, outgoing_tangent

Segment = LineSegment | CubicSegment

SMOOTH_DEG = 0.5
KINK_MAX_DEG = 30.0
TERMINAL_RANGE = (85.0, 95.0)


def _angle_between(a: Point, b: Point) -> float | None:
    la = math.hypot(a.x, a.y)
    lb = math.hypot(b.x, b.y)
    if la < 1e-12 or lb < 1e-12:
        return None
    d = max(-1.0, min(1.0, (a.x * b.x + a.y * b.y) / (la * lb)))
    return math.degrees(math.acos(d))


def join_angles(contour: Contour) -> list[float]:
    """Turn angle in degrees at each join ``i`` (end of seg i → start of i+1)."""
    segs = contour.segments
    n = len(segs)
    out: list[float] = []
    for i in range(n if contour.closed else n - 1):
        ang = _angle_between(incoming_tangent(segs[i]), outgoing_tangent(segs[(i + 1) % n]))
        out.append(180.0 if ang is None else ang)
    return out


@dataclass(frozen=True, slots=True)
class JoinCounts:
    """Join census: smooth, unintended kinks, terminal corners, other corners."""

    smooth: int
    kinks: int
    terminals: int
    corners: int

    @property
    def total(self) -> int:
        return self.smooth + self.kinks + self.terminals + self.corners

    @property
    def non_g1(self) -> int:
        return self.kinks + self.terminals + self.corners


def _is_line(seg: Segment) -> bool:
    return isinstance(seg, LineSegment)


def classify_joins(outline: Outline) -> JoinCounts:
    """Classify joins.

    - ``smooth``: turn < 0.5°
    - ``kinks``: 0.5°–30° — almost-smooth breaks; never intended
    - ``terminals``: ≈90° between two straight segments (flat stroke ends)
    - ``corners``: everything else (crotches, notches, unblended joins)
    """
    smooth = kinks = terminals = corners = 0
    for contour in outline.contours:
        segs = contour.segments
        n = len(segs)
        for i, ang in enumerate(join_angles(contour)):
            a, b = segs[i], segs[(i + 1) % n]
            if ang < SMOOTH_DEG:
                smooth += 1
            elif ang <= KINK_MAX_DEG:
                kinks += 1
            elif TERMINAL_RANGE[0] <= ang <= TERMINAL_RANGE[1] and _is_line(a) and _is_line(b):
                terminals += 1
            else:
                corners += 1
    return JoinCounts(smooth, kinks, terminals, corners)


# --- trimming helpers -------------------------------------------------------


def _seg_end(seg: Segment) -> Point:
    return seg.p1 if isinstance(seg, LineSegment) else seg.p3


def _dist(a: Point, b: Point) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def _chord(seg: Segment) -> float:
    return _dist(seg.p0, _seg_end(seg))


def _cubic_at(seg: CubicSegment, t: float) -> Point:
    mt = 1.0 - t
    p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
    x = mt**3 * p0.x + 3 * mt * mt * t * p1.x + 3 * mt * t * t * p2.x + t**3 * p3.x
    y = mt**3 * p0.y + 3 * mt * mt * t * p1.y + 3 * mt * t * t * p2.y + t**3 * p3.y
    return Point(x, y)


def _t_at_distance(seg: Segment, d: float, *, from_end: bool) -> float:
    """Parameter whose point lies ``d`` (chord) from the chosen endpoint."""
    anchor = _seg_end(seg) if from_end else seg.p0
    if isinstance(seg, LineSegment):
        length = _chord(seg)
        f = min(1.0, d / length) if length > 1e-12 else 0.0
        return 1.0 - f if from_end else f
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2.0
        t = 1.0 - mid if from_end else mid
        if _dist(_cubic_at(seg, t), anchor) < d:
            lo = mid
        else:
            hi = mid
    mid = (lo + hi) / 2.0
    return 1.0 - mid if from_end else mid


def _split(seg: Segment, t: float) -> tuple[Segment, Segment]:
    if isinstance(seg, LineSegment):
        m = Point(seg.p0.x + (seg.p1.x - seg.p0.x) * t, seg.p0.y + (seg.p1.y - seg.p0.y) * t)
        return LineSegment(seg.p0, m), LineSegment(m, seg.p1)
    pts = [p.as_tuple() for p in seg.points]
    a, b = splitCubicAtT(*pts, t)
    return (
        CubicSegment(*(Point(*p) for p in a)),
        CubicSegment(*(Point(*p) for p in b)),
    )


def _line_intersection(p: Point, dp: Point, q: Point, dq: Point) -> Point | None:
    den = dp.x * dq.y - dp.y * dq.x
    if abs(den) < 1e-12:
        return None
    s = ((q.x - p.x) * dq.y - (q.y - p.y) * dq.x) / den
    if s <= 0:
        return None
    return Point(p.x + dp.x * s, p.y + dp.y * s)


def _bridge(a_end: Segment, b_start: Segment, tension: float) -> CubicSegment:
    """Cubic from end of ``a_end`` to start of ``b_start`` (handles at tangent hit)."""
    A = _seg_end(a_end)
    B = b_start.p0
    ta = incoming_tangent(a_end)
    tb = outgoing_tangent(b_start)
    X = _line_intersection(A, ta, B, Point(-tb.x, -tb.y))
    if X is None:
        k = _dist(A, B) * 0.55
        la = math.hypot(ta.x, ta.y) or 1.0
        lb = math.hypot(tb.x, tb.y) or 1.0
        p1 = Point(A.x + ta.x / la * k, A.y + ta.y / la * k)
        p2 = Point(B.x - tb.x / lb * k, B.y - tb.y / lb * k)
        return CubicSegment(A, p1, p2, B)
    # tension=1 → both handles at X (G2 against lines); <1 pulls them back.
    p1 = Point(A.x + (X.x - A.x) * tension, A.y + (X.y - A.y) * tension)
    p2 = Point(B.x + (X.x - B.x) * tension, B.y + (X.y - B.y) * tension)
    return CubicSegment(A, p1, p2, B)


CornerSelector = Callable[[float, Segment, Segment], bool]


def default_selector(angle: float, a: Segment, b: Segment) -> bool:
    """Blend kinks and corners; leave smooth joins and flat terminals alone."""
    if angle < SMOOTH_DEG:
        return False
    is_terminal = TERMINAL_RANGE[0] <= angle <= TERMINAL_RANGE[1] and _is_line(a) and _is_line(b)
    return not is_terminal


def blend_contour(
    contour: Contour,
    radius: float,
    *,
    select: CornerSelector = default_selector,
    tension: float = 1.0,
    max_fraction: float = 0.45,
) -> Contour:
    """Blend selected corners of one closed contour with tangent-meeting cubics."""
    if not contour.closed or len(contour.segments) < 2:
        return contour
    segs = list(contour.segments)
    n = len(segs)
    angles = join_angles(contour)
    chosen = [select(angles[i], segs[i], segs[(i + 1) % n]) for i in range(n)]
    if not any(chosen):
        return contour
    # Trim distances per join, limited by both neighbours (shared budget).
    d = [0.0] * n
    for i in range(n):
        if chosen[i]:
            a, b = segs[i], segs[(i + 1) % n]
            d[i] = min(radius, _chord(a) * max_fraction, _chord(b) * max_fraction)
    # Trim each segment at both ends: start trimmed by join i-1, end by join i.
    trimmed: list[Segment] = []
    for i, seg in enumerate(segs):
        start_d = d[(i - 1) % n]
        end_d = d[i]
        s = seg
        if start_d > 0:
            t0 = _t_at_distance(s, start_d, from_end=False)
            s = _split(s, t0)[1]
        if end_d > 0:
            t1 = _t_at_distance(s, end_d, from_end=True)
            s = _split(s, t1)[0]
        trimmed.append(s)
    out: list[Segment] = []
    for i in range(n):
        out.append(trimmed[i])
        if d[i] > 0:
            out.append(_bridge(trimmed[i], trimmed[(i + 1) % n], tension))
    return Contour(tuple(out), closed=True)


def blend_corners(
    outline: Outline,
    radius: float,
    *,
    select: CornerSelector = default_selector,
    tension: float = 1.0,
) -> Outline:
    """Blend corners on every contour (default: all non-terminal breaks).

    ``radius`` is the trim distance along each neighbour (design units).
    ``tension`` 1.0 gives the G2-to-lines blend; 0.6–0.8 is rounder.
    """
    return Outline(
        tuple(blend_contour(c, radius, select=select, tension=tension) for c in outline.contours)
    )


def angle_range(lo: float, hi: float) -> CornerSelector:
    """Selector for joins whose turn angle is within ``[lo, hi]`` degrees."""

    def _sel(angle: float, a: Segment, b: Segment) -> bool:
        del a, b
        return lo <= angle <= hi

    return _sel


# --- G2 diagnostic ----------------------------------------------------------


def _end_curvature(seg: Segment, *, at_end: bool) -> float:
    if isinstance(seg, LineSegment):
        return 0.0
    if at_end:
        p0, p1, p2 = seg.p3, seg.p2, seg.p1
    else:
        p0, p1, p2 = seg.p0, seg.p1, seg.p2
    v1 = Point(p1.x - p0.x, p1.y - p0.y)
    v2 = Point(p2.x - p1.x, p2.y - p1.y)
    l1 = math.hypot(v1.x, v1.y)
    if l1 < 1e-9:
        return 0.0
    cross = abs(v1.x * v2.y - v1.y * v2.x)
    return (2.0 / 3.0) * cross / (l1**3)


def curvature_jump(outline: Outline) -> float:
    """Largest |Δκ|·stem-free scale at smooth joins (radius-normalised).

    Returned value is ``max |κ_in − κ_out| / max(κ_in, κ_out)`` over joins that
    are already G1 (relative jump in ``[0, 1]``; 0 means G2).
    """
    worst = 0.0
    for contour in outline.contours:
        segs = contour.segments
        n = len(segs)
        for i, ang in enumerate(join_angles(contour)):
            if ang >= SMOOTH_DEG:
                continue
            k_in = _end_curvature(segs[i], at_end=True)
            k_out = _end_curvature(segs[(i + 1) % n], at_end=False)
            top = max(k_in, k_out)
            if top < 1e-9:
                continue
            worst = max(worst, abs(k_in - k_out) / top)
    return worst
