"""Unit tests for the opt-in rounding helpers."""

from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.point import Point
from typekernel.geo.rounding import quantize, quantize_point


def test_quantize_default_is_three_digits() -> None:
    assert quantize(1.23456) == 1.235


def test_quantize_honours_ndigits() -> None:
    assert quantize(1.23456, 0) == 1.0
    assert quantize(1.23456, 1) == 1.2
    assert quantize(1.23456, 4) == 1.2346


def test_quantize_leaves_short_values_unchanged() -> None:
    assert quantize(1.5) == 1.5
    assert quantize(-0.25) == -0.25


def test_quantize_uses_python_round_half_to_even() -> None:
    """Documented tie-breaking: banker's rounding, NOT OpenType's otRound."""
    assert quantize(0.5, 0) == 0.0
    assert quantize(1.5, 0) == 2.0
    assert quantize(2.5, 0) == 2.0
    assert quantize(3.5, 0) == 4.0


def test_quantize_differs_from_opentype_rounding_on_ties() -> None:
    """Guards the documented trap: font units need otRound, not quantize."""
    from fontTools.misc.roundTools import otRound

    assert quantize(2.5, 0) == 2.0
    assert otRound(2.5) == 3
    assert quantize(-2.5, 0) == -2.0
    assert otRound(-2.5) == -2


def test_quantize_is_deterministic() -> None:
    value = 0.123456789
    assert len({quantize(value) for _ in range(50)}) == 1


def test_quantize_point_returns_a_new_quantised_point() -> None:
    original = Point(1.23456, -7.89012)
    result = quantize_point(original)
    assert result == Point(1.235, -7.89)
    assert original == Point(1.23456, -7.89012)


def test_quantize_point_honours_ndigits() -> None:
    assert quantize_point(Point(1.23456, 2.34567), 1) == Point(1.2, 2.3)


def test_builder_does_not_quantize_by_default() -> None:
    """Rounding is opt-in; the builder must return coordinates verbatim."""
    b = PathBuilder()
    b.moveTo(0.123456789, 0.0)
    b.lineTo(1.987654321, 0.0)
    contour = b.build().contours[0]
    assert contour.segments[0].p0 == Point(0.123456789, 0.0)
    assert contour.segments[0].p1 == Point(1.987654321, 0.0)
