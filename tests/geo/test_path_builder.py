"""Unit tests for the PathBuilder state machine."""

import pytest

from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment


def test_line_only_closed_contour() -> None:
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(1.0, 0.0)
    b.lineTo(1.0, 1.0)
    b.closePath()
    outline = b.build()
    assert outline.contour_count == 1
    contour = outline.contours[0]
    assert contour.closed is True
    assert [s.kind for s in contour.segments] == ["line", "line", "line"]


def test_close_path_appends_the_implicit_closing_segment() -> None:
    """A closed contour must satisfy the model's own closure invariant."""
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(1.0, 0.0)
    b.lineTo(1.0, 1.0)
    b.closePath()
    contour = b.build().contours[0]
    contour.assert_closed_consistent()
    assert contour.segments[-1].points[-1] == contour.segments[0].points[0]
    assert contour.segments[-1] == LineSegment(Point(1.0, 1.0), Point(0.0, 0.0))


def test_close_path_adds_no_segment_when_already_at_the_start() -> None:
    """A cubic loop that ends where it began needs no degenerate closing line."""
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.curveTo(0.0, 1.0, 1.0, 1.0, 0.0, 0.0)
    b.closePath()
    contour = b.build().contours[0]
    assert [s.kind for s in contour.segments] == ["cubic"]
    contour.assert_closed_consistent()


def test_cubic_path() -> None:
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.curveTo(0.0, 1.0, 1.0, 1.0, 1.0, 0.0)
    b.curveTo(1.0, -1.0, 0.0, -1.0, 0.0, 0.0)
    b.closePath()
    contour = b.build().contours[0]
    assert [s.kind for s in contour.segments] == ["cubic", "cubic"]
    assert contour.segments[0] == CubicSegment(
        Point(0.0, 0.0), Point(0.0, 1.0), Point(1.0, 1.0), Point(1.0, 0.0)
    )
    contour.assert_closed_consistent()


def test_two_contours() -> None:
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(1.0, 0.0)
    b.lineTo(1.0, 1.0)
    b.closePath()
    b.moveTo(5.0, 5.0)
    b.lineTo(6.0, 5.0)
    b.closePath()
    outline = b.build()
    assert outline.contour_count == 2
    assert all(c.closed for c in outline.contours)


def test_open_path_is_kept_as_an_open_contour() -> None:
    """Policy: an unfinished contour is kept, not dropped and not an error."""
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(1.0, 0.0)
    outline = b.build()
    assert outline.contour_count == 1
    assert outline.contours[0].closed is False
    assert len(outline.contours[0].segments) == 1


def test_move_to_finishes_the_previous_contour_as_open() -> None:
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(1.0, 0.0)
    b.moveTo(9.0, 9.0)
    b.lineTo(10.0, 9.0)
    outline = b.build()
    assert outline.contour_count == 2
    assert [c.closed for c in outline.contours] == [False, False]


def test_contours_without_segments_are_not_emitted() -> None:
    """A start point with no segments carries no geometry, so it is dropped."""
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.moveTo(1.0, 1.0)
    b.closePath()
    assert b.build().contour_count == 0


def test_build_is_non_destructive_and_idempotent() -> None:
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(1.0, 0.0)
    b.closePath()
    first = b.build()
    assert first == b.build()
    assert first.contour_count == 1


def test_build_is_empty_before_any_move_to() -> None:
    assert PathBuilder().build().contour_count == 0


def test_line_to_without_move_to_raises() -> None:
    with pytest.raises(ValueError, match="moveTo"):
        PathBuilder().lineTo(0.0, 0.0)


def test_curve_to_without_move_to_raises() -> None:
    with pytest.raises(ValueError, match="moveTo"):
        PathBuilder().curveTo(0.0, 0.0, 1.0, 1.0, 2.0, 2.0)


def test_close_path_without_move_to_raises() -> None:
    with pytest.raises(ValueError, match="moveTo"):
        PathBuilder().closePath()
