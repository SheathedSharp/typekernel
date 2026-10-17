"""Synthetic fixtures for diagonal stem compensation."""

from __future__ import annotations

import math

import pytest

from typekernel.optics.stem import diagonal_compensation, measure_oriented_stem
from typekernel.parts import DesignContext, diagonal_stem, vertical_stem


def test_compensation_vertical_is_identity() -> None:
    assert diagonal_compensation(0.0, 80.0) == pytest.approx(80.0)
    assert diagonal_compensation(0.0, 80.0, contrast=0.5) == pytest.approx(80.0)


def test_compensation_thins_diagonal() -> None:
    v = diagonal_compensation(0.0, 80.0)
    d45 = diagonal_compensation(45.0, 80.0)
    assert d45 < v
    assert d45 == pytest.approx(80.0 * math.cos(math.radians(45.0)), rel=1e-6)


def test_compensation_floor_and_contrast() -> None:
    # Near-horizontal without floor would vanish; floor clamps cos term
    w = diagonal_compensation(90.0, 80.0, floor=0.55, contrast=1.0)
    assert w == pytest.approx(80.0 * 0.55)
    # contrast leans thinner toward horizontal
    w_c = diagonal_compensation(90.0, 80.0, floor=0.55, contrast=0.5)
    assert w_c < w


def test_compensation_rejects_bad_args() -> None:
    with pytest.raises(ValueError):
        diagonal_compensation(45.0, 0.0)
    with pytest.raises(ValueError):
        diagonal_compensation(45.0, 80.0, contrast=0.0)
    with pytest.raises(ValueError):
        diagonal_compensation(45.0, 80.0, floor=0.0)


def test_compensated_slash_matches_vertical_optical_width() -> None:
    """/ bar with compensate=True locks oriented width to vertical target."""
    ctx = DesignContext.geometric_sans().tuned(stem=80.0, contrast=1.0)
    upright = vertical_stem(ctx, 0.0, 0.0, 200.0)
    # 45° slash from (0,0) to (200,200)
    slash = diagonal_stem(ctx, 0.0, 0.0, 200.0, 200.0, compensate=True)
    raw = diagonal_stem(ctx, 0.0, 0.0, 200.0, 200.0, compensate=False)

    mid_u = (40.0, 100.0)
    w_u = measure_oriented_stem(upright, mid_u, 90.0)
    assert w_u is not None
    assert w_u == pytest.approx(80.0, abs=0.6)

    mid_s = (100.0, 100.0)
    w_comp = measure_oriented_stem(slash, mid_s, 45.0)
    w_raw = measure_oriented_stem(raw, mid_s, 45.0)
    assert w_comp is not None and w_raw is not None
    # Compensated is thinner than raw constant-stem diagonal
    assert w_comp < w_raw - 1.0
    # And matches the compensation formula
    expected = diagonal_compensation(45.0, 80.0, contrast=1.0)
    assert w_comp == pytest.approx(expected, abs=0.8)


def test_compensated_x_bars() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=70.0)
    # Two crossing bars like X
    a = diagonal_stem(ctx, 0.0, 0.0, 200.0, 200.0, compensate=True)
    b = diagonal_stem(ctx, 0.0, 200.0, 200.0, 0.0, compensate=True)
    wa = measure_oriented_stem(a, (100.0, 100.0), 45.0)
    wb = measure_oriented_stem(b, (100.0, 100.0), -45.0)
    assert wa is not None and wb is not None
    target = diagonal_compensation(45.0, 70.0, contrast=ctx.contrast)
    assert wa == pytest.approx(target, abs=1.0)
    assert wb == pytest.approx(target, abs=1.0)


def test_vertical_equiv_inverts_compensation() -> None:
    from typekernel.optics.stem import diagonal_compensation, vertical_equiv_from_diagonal

    stem = 120.0
    diag = diagonal_compensation(45.0, stem)
    assert vertical_equiv_from_diagonal(diag, 45.0) == pytest.approx(stem, rel=1e-9)
