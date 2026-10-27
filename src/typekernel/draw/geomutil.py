"""Small segment/point helpers shared by Fragment, Writer, and Drawing."""

from __future__ import annotations

from collections.abc import Callable

from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

Segment = LineSegment | CubicSegment

CHAIN_TOL = 1e-9


def segment_start(seg: Segment) -> Point:
    return seg.p0


def segment_end(seg: Segment) -> Point:
    return seg.p1 if isinstance(seg, LineSegment) else seg.p3


def points_close(a: Point, b: Point, tol: float = CHAIN_TOL) -> bool:
    return abs(a.x - b.x) <= tol and abs(a.y - b.y) <= tol


def reverse_segment(seg: Segment) -> Segment:
    if isinstance(seg, LineSegment):
        return LineSegment(seg.p1, seg.p0)
    return CubicSegment(seg.p3, seg.p2, seg.p1, seg.p0)


def map_segment(seg: Segment, fn: Callable[[Point], Point]) -> Segment:
    if isinstance(seg, LineSegment):
        return LineSegment(fn(seg.p0), fn(seg.p1))
    return CubicSegment(fn(seg.p0), fn(seg.p1), fn(seg.p2), fn(seg.p3))
