"""Unit tests for the Point value type."""

from dataclasses import FrozenInstanceError

import pytest

from typekernel.geo.point import Point


def test_construction_keeps_coordinates() -> None:
    p = Point(1.5, -2.25)
    assert p.x == 1.5
    assert p.y == -2.25


def test_int_coordinates_compare_equal_to_floats() -> None:
    """No coercion happens; ints are stored as given and still compare by value."""
    assert Point(1, 2) == Point(1.0, 2.0)


def test_equality_is_by_value() -> None:
    assert Point(1.0, 2.0) == Point(1.0, 2.0)


def test_equality_distinguishes_swapped_coordinates() -> None:
    assert Point(1.0, 2.0) != Point(2.0, 1.0)


def test_is_not_equal_to_a_bare_tuple() -> None:
    """Point is deliberately not a tuple; as_tuple() is the explicit bridge."""
    assert Point(1.0, 2.0) != (1.0, 2.0)


def test_frozen_blocks_reassignment() -> None:
    p = Point(1.0, 2.0)
    with pytest.raises(FrozenInstanceError):
        p.x = 3.0
    with pytest.raises(FrozenInstanceError):
        p.y = 3.0


def test_as_tuple_returns_plain_float_pair() -> None:
    p = Point(1.0, 2.0)
    result = p.as_tuple()
    assert result == (1.0, 2.0)
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_hashable_and_usable_as_a_dict_key() -> None:
    """Documented promise: points can key a set/dict, e.g. to dedupe endpoints."""
    assert len({Point(0.0, 0.0), Point(0.0, 0.0)}) == 1
    assert {Point(0.0, 0.0): "origin"}[Point(0.0, 0.0)] == "origin"
