"""Tests for OpticalContext defaults."""

import dataclasses

import pytest

from typekernel.optics.context import OpticalContext


def test_defaults_match_upm_1000_sketch() -> None:
    ctx = OpticalContext()
    assert ctx.units_per_em == 1000.0
    assert ctx.x_height == 500.0
    assert ctx.cap_height == 700.0
    assert ctx.overshoot_round == 12.0
    assert ctx.overshoot_sharp == 0.0


def test_context_is_frozen() -> None:
    ctx = OpticalContext()
    with pytest.raises(dataclasses.FrozenInstanceError):
        ctx.overshoot_round = 99.0  # type: ignore[misc]
