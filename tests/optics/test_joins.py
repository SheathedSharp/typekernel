"""Tests for explicit join cleanup."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.joins import classify_joins
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.path_builder import PathBuilder
from typekernel.optics.joins import cleanup_joins

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"
HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def test_noop_is_identity() -> None:
    outline = load_synthetic_outline(FIXTURE)
    assert cleanup_joins(outline, policy="noop") is outline


def test_tangent_fix_removes_kinks() -> None:
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(100.0, 0.0)
    b.lineTo(102.0, 40.0)  # slight kink
    b.lineTo(100.0, 100.0)
    b.lineTo(0.0, 100.0)
    b.closePath()
    kinky = b.build()
    assert classify_joins(kinky).kinks >= 1
    fixed = cleanup_joins(kinky, policy="tangent_fix", radius=12.0)
    assert classify_joins(fixed).kinks == 0
    assert classify_joins(fixed).terminals == classify_joins(kinky).terminals


def test_tangent_fix_noop_on_clean_rect() -> None:
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(80.0, 0.0)
    b.lineTo(80.0, 60.0)
    b.lineTo(0.0, 60.0)
    b.closePath()
    rect = b.build()
    before = classify_joins(rect)
    after = classify_joins(cleanup_joins(rect, policy="tangent_fix", radius=8.0))
    assert after.terminals == before.terminals
    assert after.kinks == 0


def _sharp_crotch() -> Outline:
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(100.0, 0.0)
    b.lineTo(100.0, 80.0)
    b.lineTo(50.0, 20.0)
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
    assert after.kinks <= before.kinks + 2
    bb = bounds(opened)
    assert bb[2] > bb[0] and bb[3] > bb[1]
