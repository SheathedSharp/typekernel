"""Tests for the optics.apply pipeline."""

from pathlib import Path

from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.outline import bounds
from typekernel.optics.context import OpticalContext
from typekernel.optics.pipeline import apply

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def test_overshoot_true_changes_bounds() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=12.0)
    before = bounds(outline)
    after = bounds(apply(outline, ctx, overshoot=True))
    assert after[3] == before[3] + 12.0
    assert after[1] == before[1] - 12.0


def test_overshoot_false_is_identity() -> None:
    outline = load_synthetic_outline(FIXTURE)
    ctx = OpticalContext(overshoot_round=12.0)
    result = apply(outline, ctx, overshoot=False)
    assert result is outline
    assert bounds(result) == bounds(outline)
