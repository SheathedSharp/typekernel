"""Unit tests for the cu2qu bridge."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from typekernel.geo.contour import Contour
from typekernel.geo.convert_quadratic import (
    QuadraticContour,
    to_quadratic,
)
from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def _o_outline() -> Outline:
    return load_synthetic_outline(FIXTURE)


def test_conversion_runs_on_the_synthetic_o() -> None:
    contours, report = to_quadratic(_o_outline(), budget=1.0)
    assert len(contours) == 2
    assert report.segment_count_in == 8
    assert report.segment_count_out >= 8


def test_report_carries_budget_and_max_error() -> None:
    _, report = to_quadratic(_o_outline(), budget=0.5)
    assert report.budget == 0.5
    assert report.max_error >= 0.0


def test_measured_error_stays_within_the_budget() -> None:
    """cu2qu promises the budget as an upper bound; our measurement must agree."""
    for budget in (2.0, 1.0, 0.5, 0.1):
        _, report = to_quadratic(_o_outline(), budget=budget)
        assert report.max_error <= budget


def test_a_tighter_budget_costs_more_segments() -> None:
    _, loose = to_quadratic(_o_outline(), budget=4.0)
    _, tight = to_quadratic(_o_outline(), budget=0.05)
    assert tight.segment_count_out > loose.segment_count_out
    assert tight.max_error < loose.max_error


def test_closed_flags_are_preserved() -> None:
    contours, _ = to_quadratic(_o_outline())
    assert [contour.closed for contour in contours] == [True, True]


def test_splines_use_the_implied_on_curve_convention() -> None:
    """A spline of n quadratics is n+2 points: on, n off-curve, on."""
    contours, _ = to_quadratic(_o_outline(), budget=1.0)
    for contour in contours:
        assert len(contour.splines) == 4
        for spline in contour.splines:
            assert len(spline) >= 3
            assert contour.quadratic_count >= 4


def test_spline_endpoints_match_the_source_cubic() -> None:
    contours, _ = to_quadratic(_o_outline(), budget=1.0)
    source = _o_outline().contours[0].segments
    for spline, segment in zip(contours[0].splines, source, strict=True):
        assert spline[0] == segment.p0.as_tuple()
        assert spline[-1] == segment.p3.as_tuple()


def test_straight_segments_convert_exactly() -> None:
    """A line needs no approximation: it becomes a degenerate quadratic."""
    outline = Outline(
        (Contour((LineSegment(Point(0.0, 0.0), Point(10.0, 0.0)),), closed=False),)
    )
    contours, report = to_quadratic(outline)
    spline = contours[0].splines[0]
    assert spline == ((0.0, 0.0), (5.0, 0.0), (10.0, 0.0))
    assert report.segment_count_in == 1
    assert report.segment_count_out == 1
    assert report.max_error == 0.0


def test_empty_outline_converts_to_nothing() -> None:
    contours, report = to_quadratic(Outline(()))
    assert contours == ()
    assert report.segment_count_in == 0
    assert report.segment_count_out == 0


def test_quadratic_contour_is_a_frozen_value() -> None:
    contours, _ = to_quadratic(_o_outline())
    assert isinstance(contours[0], QuadraticContour)
    with pytest.raises(FrozenInstanceError):
        contours[0].closed = False


def test_conversion_is_deterministic() -> None:
    first_contours, first_report = to_quadratic(_o_outline(), budget=0.75)
    second_contours, second_report = to_quadratic(_o_outline(), budget=0.75)
    assert first_contours == second_contours
    assert first_report == second_report


def test_uses_fonttools_cu2qu_not_a_local_reimplementation() -> None:
    """The bridge must delegate: cu2qu's own error type must surface."""
    from fontTools.cu2qu.errors import ApproxNotFoundError

    # An impossible budget must raise cu2qu's own error, not a home-grown one.
    with pytest.raises(ApproxNotFoundError):
        to_quadratic(
            Outline(
                (
                    Contour(
                        (
                            CubicSegment(
                                Point(0.0, 0.0),
                                Point(0.0, 1.0),
                                Point(1.0, 1.0),
                                Point(1.0, 0.0),
                            ),
                        ),
                        closed=False,
                    ),
                )
            ),
            budget=1e-12,
        )
