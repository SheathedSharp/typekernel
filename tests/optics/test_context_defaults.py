"""Tests for OpticalContext.latin_defaults()."""

from typekernel.optics.context import OpticalContext


def test_latin_defaults_positive_with_round_overshoot() -> None:
    ctx = OpticalContext.latin_defaults()
    assert ctx.units_per_em > 0
    assert ctx.x_height > 0
    assert ctx.cap_height > 0
    assert ctx.overshoot_round > 0
    assert ctx.overshoot_sharp >= 0
    assert ctx.cap_height > ctx.x_height
