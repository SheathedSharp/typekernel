"""Unit tests for the contour winding / signed-area helper."""

from pathlib import Path

from fontTools.pens.areaPen import AreaPen

from typekernel.geo.contour import Contour, signed_area
from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.outline import Outline
from typekernel.geo.pens import draw_outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"

CCW_SQUARE = (Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10))


def _polygon(points: tuple[Point, ...], *, closed: bool = True) -> Contour:
    segments = [
        LineSegment(start, end)
        for start, end in zip(points, (*points[1:], points[0]), strict=True)
    ]
    return Contour(tuple(segments), closed=closed)


def _exact_area(contour: Contour) -> float:
    """True signed area of the contour's curves, via fontTools."""
    pen = AreaPen()
    draw_outline(Outline((contour,)), pen)
    return pen.value


def test_counter_clockwise_square_is_positive() -> None:
    assert signed_area(_polygon(CCW_SQUARE)) == 100.0


def test_clockwise_square_is_negative() -> None:
    assert signed_area(_polygon(tuple(reversed(CCW_SQUARE)))) == -100.0


def test_degenerate_contours_have_zero_area() -> None:
    assert signed_area(Contour((), closed=True)) == 0.0
    assert signed_area(_polygon((Point(0, 0), Point(1, 1)))) == 0.0


def test_open_and_closed_polygons_agree() -> None:
    """An open contour is treated as if closed by one implicit straight edge."""
    assert signed_area(_polygon(CCW_SQUARE, closed=False)) == 100.0


def test_synthetic_o_outer_is_ccw_and_counter_is_cw() -> None:
    outer, counter = load_synthetic_outline(FIXTURE).contours
    assert signed_area(outer) > 0
    assert signed_area(counter) < 0


def test_sign_agrees_with_fonttools_exact_signed_area() -> None:
    """The cheap polygon pass must at least get the orientation right."""
    for contour in load_synthetic_outline(FIXTURE).contours:
        assert (signed_area(contour) > 0) == (_exact_area(contour) > 0)


def test_polygon_approximation_understates_the_true_area() -> None:
    """Documented caveat: the magnitude is not the enclosed area."""
    outer = load_synthetic_outline(FIXTURE).contours[0]
    assert abs(signed_area(outer)) < abs(_exact_area(outer))


def test_cubic_handles_do_not_change_the_sign() -> None:
    """A bulging cubic contour keeps the orientation of its on-curve polygon."""
    square = _polygon(CCW_SQUARE)
    bulged = Contour(
        tuple(
            CubicSegment(
                segment.p0,
                Point(segment.p0.x + 1.0, segment.p0.y + 1.0),
                Point(segment.p1.x + 1.0, segment.p1.y + 1.0),
                segment.p1,
            )
            for segment in square.segments
        ),
        closed=True,
    )
    assert signed_area(bulged) == signed_area(square)
