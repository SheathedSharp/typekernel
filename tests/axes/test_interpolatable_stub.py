"""Tests for the interpolatable topology hook."""

from __future__ import annotations

from tests.axes._rect_helpers import closed_rect
from typekernel.axes.interpolatable import check_interpolatable
from typekernel.geo.outline import Outline


def test_compatible_outlines_return_empty() -> None:
    a = closed_rect(0, 0, 10, 10)
    b = closed_rect(-1, -1, 11, 11)
    assert check_interpolatable([a, b]) == []


def test_contour_mismatch_reported() -> None:
    a = closed_rect(0, 0, 10, 10)
    b = Outline(a.contours + a.contours)
    problems = check_interpolatable([a, b])
    assert problems
    assert "contour count" in problems[0]


def test_docstring_mentions_fonttools() -> None:
    assert "fontTools.varLib.interpolatable" in (check_interpolatable.__doc__ or "")
