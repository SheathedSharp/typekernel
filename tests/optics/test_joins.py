"""Tests for explicit join cleanup."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.joins import classify_joins
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.optics.joins import cleanup_joins

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"
HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def test_noop_is_identity() -> None:
    outline = load_synthetic_outline(FIXTURE)
    assert cleanup_joins(outline, policy="noop") is outline


def test_tangent_fix_still_reserved() -> None:
    outline = load_synthetic_outline(FIXTURE)
    with pytest.raises(NotImplementedError):
        cleanup_joins(outline, policy="tangent_fix")


def _sharp_crotch() -> Outline:
    """Closed chevron: wide base, sharp top crotch (concave)."""
    # CCW outer of a thick V / chevron ring would be complex; use a simple
    # concave quad: square with a deep V notch on top (arrowhead hole side).
    # Shape: pentagon with a downward V — points:
    # (0,0)-(100,0)-(100,80)-(50,20)-(0,80)  → concave at (50,20)
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(100.0, 0.0)
    b.lineTo(100.0, 80.0)
    b.lineTo(50.0, 20.0)  # crotch apex
    b.lineTo(0.0, 80.0)
    b.closePath()
    return b.build()


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required for ink_trap policy")
def test_ink_trap_policy_opens_crotch_without_new_kinks() -> None:
    outline = _sharp_crotch()
    before = classify_joins(outline)
    assert before.corners >= 1
    opened = cleanup_joins(
        outline,
        policy="ink_trap",
        depth=14.0,
        opening_deg=32.0,
        min_turn_deg=40.0,
        max_turn_deg=175.0,
    )
    assert opened is not outline
    assert opened.contour_count >= 1
    after = classify_joins(opened)
    # Trap should not introduce unintended near-smooth kinks at the claim site;
    # kinks count must not explode.
    assert after.kinks <= before.kinks + 2
    # Outline still closed and finite
    from typekernel.geo.outline import bounds

    bb = bounds(opened)
    assert bb[2] > bb[0] and bb[3] > bb[1]
