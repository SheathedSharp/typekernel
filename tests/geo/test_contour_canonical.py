"""Contour helpers for interpolation-stable outlines."""

from __future__ import annotations

from typekernel.geo.contour import Contour, canonical_contour_start
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment


def test_canonical_contour_start_picks_lowest_left() -> None:
    segs = (
        LineSegment(Point(10.0, 5.0), Point(10.0, 0.0)),
        LineSegment(Point(0.0, 0.0), Point(5.0, 0.0)),
        LineSegment(Point(5.0, 0.0), Point(5.0, 5.0)),
        LineSegment(Point(5.0, 5.0), Point(10.0, 5.0)),
    )
    rotated = canonical_contour_start(Contour(segs, closed=True))
    assert rotated.segments[0].points[0].x == 0.0
    assert rotated.segments[0].points[0].y == 0.0
