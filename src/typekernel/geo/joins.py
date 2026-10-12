"""Curvature-aware join blending for outlines.

Replaces "boolean union + fillet pad" patching with an explicit operator:
every selected corner is trimmed back along both neighbours and bridged by
one cubic whose two handles meet at the tangent intersection. Against
straight neighbours that cubic is **G2** (zero curvature at both ends, so no
curvature jump); against curved neighbours it is at least **G1**.

Agent-facing entry points:

- :func:`join_angles` / :func:`classify_joins` — read what a contour has
- :func:`blend_corners` — smooth chosen corners (crotches, kinks, shoulders)
- :func:`ease_curvature` — G2-harmonize straight↔curve joins (κ→0 into the line);
  clothoid-style both-end easing for G1–G1 single-cubic quarters
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


# --- straight ↔ curve curvature easing (G2 harmonize) ---------------------


def _unit(v: Point) -> Point | None:
    length = math.hypot(v.x, v.y)
    if length < 1e-12:
        return None
    return Point(v.x / length, v.y / length)


def _harmonize_cubic_at_line(
    cubic: CubicSegment,
    *,
    at_start: bool,
    line_tangent: Point,
    min_handle: float,
) -> CubicSegment:
    """Move only the *inner* off-curve onto the tangent so κ=0 at that end.

    The near handle (``p1`` at start / ``p2`` at end) is left alone so an
    already-G1 join keeps its tangent; only the far handle is projected onto
    that same ray, which is the G2 condition against a straight neighbour.
    """
    if at_start:
        # line → cubic: keep p1 (G1), put p2 on ray p0→p1.
        p0, p1, p2, p3 = cubic.p0, cubic.p1, cubic.p2, cubic.p3
        u = _unit(Point(p1.x - p0.x, p1.y - p0.y))
        if u is None:
            u = _unit(line_tangent)
        if u is None:
            return cubic
        # Match hemisphere of line_tangent when available.
        lt = _unit(line_tangent)
        if lt is not None and u.x * lt.x + u.y * lt.y < 0:
            # Near handle disagrees with the line — fall back to line tangent
            # and also snap p1 (rare; keeps the join from folding back).
            u = lt
            len1 = max(min_handle, math.hypot(p1.x - p0.x, p1.y - p0.y))
            p1 = Point(p0.x + u.x * len1, p0.y + u.y * len1)
        len1 = math.hypot(p1.x - p0.x, p1.y - p0.y)
        side2 = (p2.x - p0.x) * u.x + (p2.y - p0.y) * u.y
        len2 = max(side2, len1 * 1.01, min_handle)
        p2_new = Point(p0.x + u.x * len2, p0.y + u.y * len2)
        return CubicSegment(p0, p1, p2_new, p3)
    # cubic → line: keep p2 (G1 incoming), put p1 on ray p3←p2.
    p0, p1, p2, p3 = cubic.p0, cubic.p1, cubic.p2, cubic.p3
    u = _unit(Point(p3.x - p2.x, p3.y - p2.y))
    if u is None:
        u = _unit(line_tangent)
    if u is None:
        return cubic
    lt = _unit(line_tangent)
    if lt is not None and u.x * lt.x + u.y * lt.y < 0:
        u = lt
        len2 = max(min_handle, math.hypot(p3.x - p2.x, p3.y - p2.y))
        p2 = Point(p3.x - u.x * len2, p3.y - u.y * len2)
    len2 = math.hypot(p3.x - p2.x, p3.y - p2.y)
    back = (p3.x - p1.x) * u.x + (p3.y - p1.y) * u.y
    len1 = max(back, len2 * 1.01, min_handle)
    p1_new = Point(p3.x - u.x * len1, p3.y - u.y * len1)
    return CubicSegment(p0, p1_new, p2, p3)


def _already_g2_with_lines(cubic: CubicSegment, *, eps: float = 1e-6) -> bool:
    """True when both ends of ``cubic`` already have ~zero curvature."""
    return (
        _end_curvature(cubic, at_end=False) <= eps
        and _end_curvature(cubic, at_end=True) <= eps
    )


def _insert_line_to_curve_ease(
    line: LineSegment,
    cubic: CubicSegment,
    *,
    length: float,
    min_handle: float,
) -> tuple[LineSegment, CubicSegment, CubicSegment]:
    """Trim line+cubic and insert a G2-to-line / G1-to-curve transition cubic."""
    trim = min(length, _chord(line) * 0.45, _chord(cubic) * 0.45)
    if trim <= min_handle * 0.5:
        return line, cubic, cubic  # degenerate — caller should ignore
    # Trim line from its end
    t_line = _t_at_distance(line, trim, from_end=True)
    line_kept, _ = _split(line, t_line)
    # Trim cubic from its start
    t_cub = _t_at_distance(cubic, trim, from_end=False)
    _, cubic_rest = _split(cubic, t_cub)
    A = _seg_end(line_kept)
    B = cubic_rest.p0
    u_line = _unit(incoming_tangent(line_kept))
    u_arc = _unit(outgoing_tangent(cubic_rest))
    if u_line is None or u_arc is None:
        return line, cubic, cubic
    # P2 at intersection of line ray from A and reverse-arc ray from B
    X = _line_intersection(A, u_line, B, Point(-u_arc.x, -u_arc.y))
    if X is None:
        # Parallel: place P2 along the line, P1 halfway; G1 at B may be soft
        dist = _dist(A, B)
        X = Point(A.x + u_line.x * dist * 0.7, A.y + u_line.y * dist * 0.7)
    # κ=0 at A ⇒ P1 and X(=P2) on the line ray
    d_ax = _dist(A, X)
    p1 = Point(A.x + u_line.x * max(d_ax * 0.5, min_handle), A.y + u_line.y * max(d_ax * 0.5, min_handle))
    # Re-express P2: stay on line for κ=0; pull toward X∩ projection
    # If X is on the line ray, use it; else project X onto the line.
    side = (X.x - A.x) * u_line.x + (X.y - A.y) * u_line.y
    p2 = Point(A.x + u_line.x * max(side, d_ax * 0.55, min_handle), A.y + u_line.y * max(side, d_ax * 0.55, min_handle))
    # G1 at B: prefer handle along -u_arc — but κ=0 constraint put p2 on the
    # line. Use a compromise only when X lies near both constraints.
    if X is not None and abs((X.x - A.x) * u_line.y - (X.y - A.y) * u_line.x) < 1e-6 * max(d_ax, 1.0):
        p2 = X
    ease = CubicSegment(A, p1, p2, B)
    return line_kept, ease, cubic_rest  # type: ignore[return-value]


def _insert_curve_to_line_ease(
    cubic: CubicSegment,
    line: LineSegment,
    *,
    length: float,
    min_handle: float,
) -> tuple[CubicSegment, CubicSegment, LineSegment]:
    """Trim cubic+line and insert a G1-from-curve / G2-to-line transition."""
    trim = min(length, _chord(line) * 0.45, _chord(cubic) * 0.45)
    if trim <= min_handle * 0.5:
        return cubic, cubic, line
    t_cub = _t_at_distance(cubic, trim, from_end=True)
    cubic_kept, _ = _split(cubic, t_cub)
    t_line = _t_at_distance(line, trim, from_end=False)
    _, line_rest = _split(line, t_line)
    A = _seg_end(cubic_kept)
    B = line_rest.p0
    u_arc = _unit(incoming_tangent(cubic_kept))
    u_line = _unit(outgoing_tangent(line_rest))
    if u_arc is None or u_line is None:
        return cubic, cubic, line
    X = _line_intersection(A, u_arc, B, Point(-u_line.x, -u_line.y))
    # κ=0 at B (line): p1 and p2 on the line through B along -u_line from B...
    # Transition cubic A → B: G1 at A along u_arc, G2 at B (κ=0) along u_line.
    # Put p2 and B with p1 on the line ray ending at B.
    if X is not None:
        # Prefer X if it lies on the line through B
        side = (B.x - X.x) * u_line.x + (B.y - X.y) * u_line.y
        p2 = Point(B.x - u_line.x * max(side, min_handle), B.y - u_line.y * max(side, min_handle))
    else:
        dist = _dist(A, B)
        p2 = Point(B.x - u_line.x * dist * 0.7, B.y - u_line.y * dist * 0.7)
    d_pb = _dist(p2, B)
    p1 = Point(B.x - u_line.x * max(d_pb * 1.5, min_handle * 2), B.y - u_line.y * max(d_pb * 1.5, min_handle * 2))
    # G1 at A: first handle along u_arc — but p1 was placed for B's G2. Recompute
    # p1 as A + u_arc * h, keep p2 on line for κ=0 at B.
    h = max(min_handle, _dist(A, B) * 0.4)
    p1 = Point(A.x + u_arc.x * h, A.y + u_arc.y * h)
    # p2 stays on line before B
    p2 = Point(B.x - u_line.x * max(d_pb, min_handle), B.y - u_line.y * max(d_pb, min_handle))
    ease = CubicSegment(A, p1, p2, B)
    return cubic_kept, ease, line_rest  # type: ignore[return-value]




def _scrub_degenerate_segments(segs: list[Segment], *, eps: float = 1e-6) -> list[Segment]:
    """Drop near-zero lines and merge collinear consecutive lines."""
    if not segs:
        return segs
    out: list[Segment] = []
    for seg in segs:
        if _is_line(seg) and _chord(seg) <= eps:
            continue
        if out and _is_line(out[-1]) and _is_line(seg):
            prev = out[-1]
            assert isinstance(prev, LineSegment) and isinstance(seg, LineSegment)
            # Merge if collinear and contiguous (same direction).
            ang = _angle_between(incoming_tangent(prev), outgoing_tangent(seg))
            if ang is not None and ang < 0.5 and _dist(_seg_end(prev), seg.p0) <= eps:
                out[-1] = LineSegment(prev.p0, seg.p1)
                continue
        out.append(seg)
    # Closed-contour wrap: merge first/last if both lines and collinear.
    if (
        len(out) >= 2
        and _is_line(out[0])
        and _is_line(out[-1])
    ):
        first, last = out[0], out[-1]
        assert isinstance(first, LineSegment) and isinstance(last, LineSegment)
        ang = _angle_between(incoming_tangent(last), outgoing_tangent(first))
        if ang is not None and ang < 0.5 and _dist(_seg_end(last), first.p0) <= eps:
            out[0] = LineSegment(last.p0, first.p1)
            out.pop()
    return out


def _insert_both_end_ease(
    line_in: LineSegment,
    cubic: CubicSegment,
    line_out: LineSegment,
    *,
    length: float,
    min_handle: float,
) -> tuple[Segment, ...] | None:
    """Clothoid-style ease at both ends of a G1–G1 single cubic between lines.

    Returns ``(line_in_kept, ease_in, mid, ease_out, line_out_rest)`` or
    ``None`` if the cubic / flanking lines are too short to trim twice.
    Each flanking line must keep a usable remnant after one trim so adjacent
    corners on a rounded rectangle do not collapse a shared side into a
    zero-length L→L kink.
    """
    chord_in = _chord(line_in)
    chord_out = _chord(line_out)
    chord_c = _chord(cubic)
    # Need enough straight run on both sides (and arc body) for two trims.
    if chord_in < length * 2.0 or chord_out < length * 2.0 or chord_c < length * 2.5:
        return None
    trim = min(length, chord_in * 0.35, chord_out * 0.35, chord_c * 0.3)
    if trim <= min_handle * 0.5 or chord_c < trim * 2.5:
        return None
    # Start: line → cubic
    line_kept, ease_in, rest_after_in = _insert_line_to_curve_ease(
        line_in, cubic, length=trim, min_handle=min_handle
    )
    if ease_in is rest_after_in or ease_in is cubic:
        return None
    # End: remaining cubic → outgoing line
    mid, ease_out, line_rest = _insert_curve_to_line_ease(
        rest_after_in, line_out, length=trim, min_handle=min_handle
    )
    if ease_out is rest_after_in or ease_out is mid:
        return None
    return (line_kept, ease_in, mid, ease_out, line_rest)


def ease_contour(
    contour: Contour,
    *,
    angle_tol: float = SMOOTH_DEG,
    min_handle: float = 1.0,
    insert_length: float | None = None,
    both_ends: bool = True,
) -> Contour:
    """Harmonize nearly-G1 straight↔arc joins on one contour.

    Strategy:
      1. Arc runs (cubic continues into another cubic): in-place handle
         projection — G2 against the line, arc body kept.
      2. Single cubic between two lines with residual κ jump: insert a short
         transition cubic (G2 to the line, G1 into the arc). When both ends
         are already G1 (quarter between two lines) and ``both_ends`` is True,
         insert clothoid-style transitions at **both** ends.
      3. Cubics already G2 to both neighbouring lines (fillets from
         :func:`blend_corners`): leave untouched.

    Flat terminals and non-smooth corners are ignored — run
    :func:`blend_corners` first for those.
    """
    if len(contour.segments) < 2:
        return contour
    segs: list[Segment] = list(contour.segments)
    n = len(segs)
    angles = join_angles(contour)
    length = insert_length if insert_length is not None else max(min_handle * 8.0, 12.0)
    # Pass 1 — in-place harmonize for cubic→cubic arc runs (indices stable).
    for i in range(n if contour.closed else n - 1):
        if angles[i] >= angle_tol:
            continue
        a, b = segs[i], segs[(i + 1) % n]
        if _is_line(a) and isinstance(b, CubicSegment):
            other = segs[(i + 2) % n]
            if isinstance(other, CubicSegment):
                segs[(i + 1) % n] = _harmonize_cubic_at_line(
                    b, at_start=True, line_tangent=incoming_tangent(a), min_handle=min_handle
                )
        elif isinstance(a, CubicSegment) and _is_line(b):
            prev = segs[(i - 1) % n]
            if isinstance(prev, CubicSegment):
                segs[i] = _harmonize_cubic_at_line(
                    a, at_start=False, line_tangent=outgoing_tangent(b), min_handle=min_handle
                )
    # Pass 2 — insert transitions for line–cubic–line arcs with κ jump.
    # Walk with a while-loop since we insert segments.
    i = 0
    segs_n = list(segs)
    nn = len(segs_n)
    visited_insert = 0
    while i < nn:
        a = segs_n[i]
        b = segs_n[(i + 1) % nn]
        c = segs_n[(i + 2) % nn]
        ang = _angle_between(incoming_tangent(a), outgoing_tangent(b))
        ang_v = 180.0 if ang is None else ang
        did = False
        far_ang = _angle_between(incoming_tangent(b), outgoing_tangent(c))
        far_v = 180.0 if far_ang is None else far_ang
        both_g1 = ang_v < angle_tol and far_v < angle_tol
        line_cubic_line = (
            _is_line(a) and isinstance(b, CubicSegment) and _is_line(c)
        )
        if (
            line_cubic_line
            and ang_v < angle_tol
            and not _already_g2_with_lines(b)  # type: ignore[arg-type]
        ):
            assert isinstance(a, LineSegment) and isinstance(b, CubicSegment)
            assert isinstance(c, LineSegment)
            if both_g1 and both_ends:
                # Clothoid both-end: ease at start and end of the quarter.
                replaced = _insert_both_end_ease(
                    a, b, c, length=length, min_handle=min_handle
                )
                if replaced is not None:
                    segs_n = segs_n[:i] + list(replaced) + segs_n[i + 3 :]
                    nn = len(segs_n)
                    did = True
                    visited_insert += 1
                    i += len(replaced) - 1  # advance past new run
            elif not both_g1:
                line_kept, ease, rest = _insert_line_to_curve_ease(
                    a, b, length=length, min_handle=min_handle
                )
                if ease is not rest and ease is not b:
                    segs_n = segs_n[:i] + [line_kept, ease, rest] + segs_n[i + 2 :]
                    nn = len(segs_n)
                    did = True
                    visited_insert += 1
                    i += 2
        if not did and (
            ang_v < angle_tol
            and isinstance(a, CubicSegment)
            and _is_line(b)
            and _is_line(segs_n[(i - 1) % nn])
            and not _already_g2_with_lines(a)
        ):
            # Single cubic between two lines, far end only (start join was not
            # G1 — otherwise the line→cubic insert above owns the span).
            prev = segs_n[(i - 1) % nn]
            prev_ang = _angle_between(incoming_tangent(prev), outgoing_tangent(a))
            prev_ang_v = 180.0 if prev_ang is None else prev_ang
            if prev_ang_v >= angle_tol:
                assert isinstance(a, CubicSegment) and isinstance(b, LineSegment)
                kept, ease, line_rest = _insert_curve_to_line_ease(
                    a, b, length=length, min_handle=min_handle
                )
                if ease is not a and ease is not kept:
                    segs_n = segs_n[:i] + [kept, ease, line_rest] + segs_n[i + 2 :]
                    nn = len(segs_n)
                    did = True
                    visited_insert += 1
                    i += 2
        if not did:
            i += 1
        if visited_insert > nn:  # safety
            break
    segs_n = _scrub_degenerate_segments(segs_n)
    return Contour(tuple(segs_n), closed=contour.closed)


def ease_curvature(
    outline: Outline,
    *,
    angle_tol: float = SMOOTH_DEG,
    min_handle: float = 1.0,
    insert_length: float | None = None,
    both_ends: bool = True,
) -> Outline:
    """G2-harmonize straight↔curve joins on every contour.

    Agent-facing counterpart to :func:`blend_corners`: that operator builds a
    fillet cubic for broken corners; this one removes the residual curvature
    jump where a straight already meets a round with matching tangents
    (stadium ends, stem-to-arc, U-bowl troughs, …).

    When ``both_ends`` is True (default), G1–G1 single-cubic quarters between
    two lines also get clothoid-style transition cubics at **both** ends
    (κ→0 into each line). Cubics already G2 to both lines (``blend_corners``
    fillets) stay untouched.

    Parameters:
        angle_tol: max turn (degrees) still treated as "already G1".
        min_handle: floor on projected handle length (design units).
        insert_length: trim length for inserted transitions on single-cubic
            arcs between two lines; ``None`` picks a small default.
        both_ends: ease both ends of G1–G1 single-cubic quarters.
    """
    return Outline(
        tuple(
            ease_contour(
                c,
                angle_tol=angle_tol,
                min_handle=min_handle,
                insert_length=insert_length,
                both_ends=both_ends,
            )
            for c in outline.contours
        )
    )


def straight_curve_jump(
    outline: Outline,
    *,
    angle_tol: float = SMOOTH_DEG,
    abs_eps: float = 1e-3,
) -> float:
    """Largest relative κ jump among smooth straight↔cubic joins only."""
    worst = 0.0
    for contour in outline.contours:
        segs = contour.segments
        n = len(segs)
        for i, ang in enumerate(join_angles(contour)):
            if ang >= angle_tol:
                continue
            a, b = segs[i], segs[(i + 1) % n]
            if not (
                (_is_line(a) and isinstance(b, CubicSegment))
                or (isinstance(a, CubicSegment) and _is_line(b))
            ):
                continue
            k_in = _end_curvature(a, at_end=True)
            k_out = _end_curvature(b, at_end=False)
            top = max(k_in, k_out)
            if top < abs_eps:
                continue
            worst = max(worst, abs(k_in - k_out) / top)
    return worst


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


def curvature_jump(outline: Outline, *, abs_eps: float = 1e-3) -> float:
    """Largest relative κ jump at smooth joins.

    ``max |κ_in − κ_out| / max(κ_in, κ_out)`` over G1 joins. Joins where both
    curvatures are below ``abs_eps`` count as matched (avoids 1.0 false
    alarms when the line side is exactly 0 and the curve side is ~1e-3).
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
            if top < abs_eps:
                continue
            worst = max(worst, abs(k_in - k_out) / top)
    return worst
