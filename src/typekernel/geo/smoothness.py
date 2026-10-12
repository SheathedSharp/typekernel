"""Join smoothness helpers (G1 tangent continuity).

These inspect or construct handle placement. They do not resample curves.
"""

from __future__ import annotations

import math

from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

Segment = LineSegment | CubicSegment


def outgoing_tangent(segment: Segment) -> Point:
    """Direction leaving the start of ``segment`` (p0 → first handle / end)."""
    if isinstance(segment, LineSegment):
        return Point(segment.p1.x - segment.p0.x, segment.p1.y - segment.p0.y)
    # Cubic: tangent at p0 is toward p1 (or p2/p3 if handles collapse).
    if segment.p1 != segment.p0:
        return Point(segment.p1.x - segment.p0.x, segment.p1.y - segment.p0.y)
    if segment.p2 != segment.p0:
        return Point(segment.p2.x - segment.p0.x, segment.p2.y - segment.p0.y)
    return Point(segment.p3.x - segment.p0.x, segment.p3.y - segment.p0.y)


def incoming_tangent(segment: Segment) -> Point:
    """Direction arriving at the end of ``segment`` (last handle → p_end)."""
    if isinstance(segment, LineSegment):
        return Point(segment.p1.x - segment.p0.x, segment.p1.y - segment.p0.y)
    if segment.p3 != segment.p2:
        return Point(segment.p3.x - segment.p2.x, segment.p3.y - segment.p2.y)
    if segment.p3 != segment.p1:
        return Point(segment.p3.x - segment.p1.x, segment.p3.y - segment.p1.y)
    return Point(segment.p3.x - segment.p0.x, segment.p3.y - segment.p0.y)


def _unit(v: Point) -> Point | None:
    length = math.hypot(v.x, v.y)
    if length < 1e-12:
        return None
    return Point(v.x / length, v.y / length)


def g1_join_error(prev: Segment, nxt: Segment) -> float:
    """Return ``1 - |dot(u_in, u_out)|`` style error in ``[0, 2]``-ish.

    Specifically ``1 - abs(dot(unit_in, unit_out))`` so 0 means parallel
    (G1 up to direction flip). Degenerate tangents return ``1.0``.
    """
    u_in = _unit(incoming_tangent(prev))
    u_out = _unit(outgoing_tangent(nxt))
    if u_in is None or u_out is None:
        return 1.0
    return 1.0 - abs(u_in.x * u_out.x + u_in.y * u_out.y)


def assert_g1_join(prev: Segment, nxt: Segment, *, tol: float = 1e-6) -> None:
    """Raise ``ValueError`` if the join is not G1 within ``tol``.

    ``tol`` is on ``g1_join_error`` (0 = perfect parallel unit tangents).
    """
    # End of prev should meet start of nxt.
    prev_end = prev.p1 if isinstance(prev, LineSegment) else prev.p3
    nxt_start = nxt.p0
    if prev_end != nxt_start:
        raise ValueError(
            f"segments do not meet: end {prev_end.as_tuple()} != start {nxt_start.as_tuple()}"
        )
    err = g1_join_error(prev, nxt)
    if err > tol:
        raise ValueError(f"join is not G1: error {err} > tol {tol}")


def is_g1_join(prev: Segment, nxt: Segment, *, tol: float = 1e-6) -> bool:
    """Return True if segments meet and share a tangent direction within ``tol``."""
    try:
        assert_g1_join(prev, nxt, tol=tol)
    except ValueError:
        return False
    return True
