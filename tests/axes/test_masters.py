"""Tests for GlyphMasters."""

from __future__ import annotations

import pytest

from tests.axes._rect_helpers import closed_rect
from typekernel.axes.masters import GlyphMasters


def test_two_weights_stored_and_fetched() -> None:
    masters = GlyphMasters()
    regular = closed_rect(0, 0, 40, 200)
    bold = closed_rect(-20, 0, 60, 200)
    masters.add({"wght": 400.0}, regular)
    masters.add({"wght": 700.0}, bold)

    assert len(masters) == 2
    assert masters.get({"wght": 400.0}) is regular
    assert masters.get({"wght": 700.0}) is bold
    assert masters.locations() == [{"wght": 400.0}, {"wght": 700.0}]


def test_missing_location_raises() -> None:
    masters = GlyphMasters()
    masters.add({"wght": 400.0}, closed_rect(0, 0, 1, 1))
    with pytest.raises(KeyError, match="no master"):
        masters.get({"wght": 700.0})
