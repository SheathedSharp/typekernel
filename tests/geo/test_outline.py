"""Unit tests for the Outline container."""

from collections.abc import Iterator
from dataclasses import FrozenInstanceError

import pytest

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

A = Point(0.0, 0.0)
B = Point(10.0, 0.0)
C = Point(0.0, 10.0)


def test_empty_outline_has_no_contours() -> None:
    assert Outline(()).contour_count == 0


def test_outline_with_one_empty_contour() -> None:
    """An empty contour is still a contour; the count must not filter it out."""
    outline = Outline((Contour((), closed=False),))
    assert outline.contour_count == 1
    assert list(outline.iter_segments()) == []


def test_contour_count_counts_all_contours() -> None:
    outline = Outline(
        (
            Contour((LineSegment(A, B), LineSegment(B, C), LineSegment(C, A)), closed=True),
            Contour((), closed=False),
        )
    )
    assert outline.contour_count == 2


def test_iter_segments_is_empty_for_an_empty_outline() -> None:
    assert list(Outline(()).iter_segments()) == []


def test_iter_segments_flattens_contours_in_order() -> None:
    first = (LineSegment(A, B), LineSegment(B, C))
    second = (CubicSegment(A, B, C, A),)
    outline = Outline((Contour(first, closed=False), Contour(second, closed=False)))
    assert list(outline.iter_segments()) == [*first, *second]


def test_iter_segments_returns_an_iterator() -> None:
    outline = Outline((Contour((LineSegment(A, B),), closed=False),))
    assert isinstance(outline.iter_segments(), Iterator)


def test_outline_is_frozen() -> None:
    outline = Outline(())
    with pytest.raises(FrozenInstanceError):
        outline.contours = ()
