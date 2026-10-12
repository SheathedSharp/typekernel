"""Unit tests for the Contour container."""

from dataclasses import FrozenInstanceError

import pytest

from typekernel.geo.contour import Contour
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

A = Point(0.0, 0.0)
B = Point(10.0, 0.0)
C = Point(0.0, 10.0)


def _triangle() -> Contour:
    return Contour(
        (LineSegment(A, B), LineSegment(B, C), LineSegment(C, A)),
        closed=True,
    )


def test_empty_contour_is_empty() -> None:
    assert Contour((), False).is_empty


def test_contour_with_segments_is_not_empty() -> None:
    assert not _triangle().is_empty


def test_triangle_retains_three_segments() -> None:
    assert len(_triangle().segments) == 3


def test_closed_flag_is_stored_and_defaults_to_false() -> None:
    assert _triangle().closed is True
    assert Contour((LineSegment(A, B),)).closed is False


def test_segments_are_retained_in_order() -> None:
    segs = (LineSegment(A, B), LineSegment(B, C), LineSegment(C, A))
    assert Contour(segs, closed=True).segments == segs


def test_cubic_segments_are_retained() -> None:
    cubic = CubicSegment(A, B, C, A)
    contour = Contour((cubic,), closed=True)
    assert contour.segments == (cubic,)
    assert contour.segments[0].kind == "cubic"


def test_contour_is_frozen() -> None:
    contour = _triangle()
    with pytest.raises(FrozenInstanceError):
        contour.closed = False


def test_closed_consistent_accepts_a_real_closed_contour() -> None:
    _triangle().assert_closed_consistent()


def test_closed_consistent_rejects_a_gap() -> None:
    gapped = Contour((LineSegment(A, B), LineSegment(B, C)), closed=True)
    with pytest.raises(ValueError):
        gapped.assert_closed_consistent()


def test_closed_consistent_ignores_open_contours() -> None:
    """An open contour makes no closure promise, so there is nothing to check."""
    Contour((LineSegment(A, B),), closed=False).assert_closed_consistent()


def test_closed_consistent_accepts_an_empty_closed_contour() -> None:
    """No endpoints exist to disagree, so an empty closed contour is not an error."""
    Contour((), closed=True).assert_closed_consistent()
