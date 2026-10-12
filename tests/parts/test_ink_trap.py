"""Synthetic ink-trap and crotch opener fixtures."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.joins import classify_joins
from typekernel.geo.outline import bounds
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts import (
    DesignContext,
    apply_ink_trap,
    crotch_join,
    crotch_opener,
    diagonal_stem,
    ink_trap,
)

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def test_ink_trap_parameters() -> None:
    ctx = DesignContext.geometric_sans()
    trap = ink_trap(
        ctx, 10.0, 20.0, depth=24.0, opening_deg=40.0, bisector_deg=270.0
    )
    assert trap.contour_count == 1
    min_x, min_y, max_x, max_y = bounds(trap)
    # Tip at (10,20), bisector down → base below tip
    assert max_y == pytest.approx(20.0, abs=0.01)
    assert min_y < 20.0 - 20.0
    assert max_x > min_x


def test_ink_trap_rejects_bad_params() -> None:
    ctx = DesignContext.geometric_sans()
    with pytest.raises(ValueError):
        ink_trap(ctx, 0.0, 0.0, depth=0.0)
    with pytest.raises(ValueError):
        ink_trap(ctx, 0.0, 0.0, opening_deg=180.0)


def test_crotch_opener_aims_into_join() -> None:
    ctx = DesignContext.geometric_sans()
    # Legs going down-left and down-right from apex (classic V crotch)
    opener = crotch_opener(ctx, 50.0, 100.0, 240.0, 300.0, depth=18.0)
    min_x, min_y, max_x, max_y = bounds(opener)
    # Bisector into black is upward (opposite crotch void below)
    assert max_y > 100.0
    assert min_y == pytest.approx(100.0, abs=0.5)
    assert max_x > min_x


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required")
def test_apply_ink_trap_opens_without_claiming_new_kinks() -> None:
    ctx = DesignContext.geometric_sans()
    # Solid concave chevron
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(120.0, 0.0)
    b.lineTo(120.0, 90.0)
    b.lineTo(60.0, 25.0)
    b.lineTo(0.0, 90.0)
    b.closePath()
    solid = b.build()
    before_kinks = classify_joins(solid).kinks
    trap = ink_trap(
        ctx, 60.0, 25.0, depth=16.0, opening_deg=30.0, bisector_deg=90.0
    )
    opened = apply_ink_trap(solid, trap)
    assert opened.contour_count >= 1
    after = classify_joins(opened)
    assert after.kinks <= before_kinks + 2
    bb = bounds(opened)
    assert bb[2] - bb[0] > 50.0


@pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required")
def test_crotch_join_two_diagonal_legs() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=60.0)
    left = diagonal_stem(ctx, 60.0, 100.0, 0.0, 0.0, compensate=True)
    right = diagonal_stem(ctx, 60.0, 100.0, 120.0, 0.0, compensate=True)
    joined = crotch_join(left, right, ctx, apex=(60.0, 100.0), depth=14.0)
    assert joined.contour_count >= 1
    bb = bounds(joined)
    assert bb[2] > bb[0]
    counts = classify_joins(joined)
    # Must not explode with near-smooth kinks at the claimed opener
    assert counts.kinks <= 4
