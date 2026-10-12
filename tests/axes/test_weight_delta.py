"""Tests for WeightDelta.from_masters and apply."""

from __future__ import annotations

import pytest

from tests.axes._rect_helpers import closed_rect
from typekernel.axes.weight_delta import WeightDelta
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment


def test_from_masters_and_apply_midpoint() -> None:
    # Regular: thin vertical stem-like rect (width 40). Bold: width 80, same height.
    regular = closed_rect(100, 100, 140, 500)
    bold = closed_rect(80, 100, 160, 500)
    delta = WeightDelta.from_masters(regular, bold)

    mid = delta.apply(regular, 0.5)
    xs = sorted({pt.x for seg in mid.iter_segments() for pt in seg.points})
    ys = sorted({pt.y for seg in mid.iter_segments() for pt in seg.points})
    assert xs == [90.0, 150.0]
    assert ys == [100.0, 500.0]


def test_apply_t0_is_identity() -> None:
    regular = closed_rect(0, 0, 100, 200)
    bold = closed_rect(-10, -10, 110, 210)
    delta = WeightDelta.from_masters(regular, bold)
    got = delta.apply(regular, 0.0)
    assert got == regular


def test_apply_t1_reaches_bold() -> None:
    regular = closed_rect(0, 0, 100, 200)
    bold = closed_rect(-10, -10, 110, 210)
    delta = WeightDelta.from_masters(regular, bold)
    got = delta.apply(regular, 1.0)
    assert got == bold


def test_contour_count_mismatch_raises() -> None:
    regular = closed_rect(0, 0, 10, 10)
    bold_extra = Outline(regular.contours + regular.contours)
    with pytest.raises(ValueError, match="contour counts"):
        WeightDelta.from_masters(regular, bold_extra)


def test_segment_kind_mismatch_raises() -> None:
    line_outline = closed_rect(0, 0, 10, 10)
    cubic = CubicSegment(Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1))
    bold_segments = (
        cubic,
        line_outline.contours[0].segments[1],
        line_outline.contours[0].segments[2],
        line_outline.contours[0].segments[3],
    )
    bold = Outline((Contour(bold_segments, closed=True),))
    with pytest.raises(ValueError, match="kind mismatch"):
        WeightDelta.from_masters(line_outline, bold)


def test_apply_rejects_incompatible_outline() -> None:
    regular = closed_rect(0, 0, 10, 10)
    bold = closed_rect(-1, -1, 11, 11)
    delta = WeightDelta.from_masters(regular, bold)
    other = Outline(regular.contours + regular.contours)
    with pytest.raises(ValueError, match="contour count"):
        delta.apply(other, 0.5)


def test_weight_delta_docstring_forbids_stroke() -> None:
    doc = (WeightDelta.__doc__ or "") + (WeightDelta.from_masters.__doc__ or "")
    module_doc = __import__("typekernel.axes.weight_delta", fromlist=["*"]).__doc__ or ""
    combined = doc + module_doc
    assert "stroke" in combined.lower() or "buffer" in combined.lower()
    assert "delta" in combined.lower()
