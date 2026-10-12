"""Unit tests for the segment types."""

from dataclasses import FrozenInstanceError

import pytest

from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

P0 = Point(0.0, 0.0)
P1 = Point(1.0, 0.0)
P2 = Point(1.0, 1.0)
P3 = Point(0.0, 1.0)


def test_line_kind() -> None:
    assert LineSegment(P0, P1).kind == "line"


def test_cubic_kind() -> None:
    assert CubicSegment(P0, P1, P2, P3).kind == "cubic"


def test_line_points_length_and_order() -> None:
    seg = LineSegment(P0, P1)
    assert len(seg.points) == 2
    assert seg.points == (P0, P1)


def test_cubic_points_length_and_order() -> None:
    seg = CubicSegment(P0, P1, P2, P3)
    assert len(seg.points) == 4
    assert seg.points == (P0, P1, P2, P3)


def test_line_equality_is_by_value() -> None:
    assert LineSegment(P0, P1) == LineSegment(P0, P1)
    assert LineSegment(P0, P1) != LineSegment(P1, P0)


def test_cubic_equality_is_by_value() -> None:
    assert CubicSegment(P0, P1, P2, P3) == CubicSegment(P0, P1, P2, P3)
    assert CubicSegment(P0, P1, P2, P3) != CubicSegment(P0, P1, P3, P2)


def test_segments_are_frozen() -> None:
    line = LineSegment(P0, P1)
    with pytest.raises(FrozenInstanceError):
        line.p0 = P2
    cubic = CubicSegment(P0, P1, P2, P3)
    with pytest.raises(FrozenInstanceError):
        cubic.p3 = P0


def test_kind_discriminates_a_heterogeneous_sequence() -> None:
    """kind exists so a contour can branch over mixed segment types."""
    segments: list[LineSegment | CubicSegment] = [
        LineSegment(P0, P1),
        CubicSegment(P0, P1, P2, P3),
    ]
    assert [s.kind for s in segments] == ["line", "cubic"]
