"""Synthetic fixtures for terminal and aperture operators."""

from __future__ import annotations

import importlib.util
import math

import pytest

from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    ball_end,
    bowl,
    flat_end,
    hook_end,
    open_bowl_ring,
    open_counter,
    shear_end,
    vertical_stem,
)

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None
pytestmark_bool = pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required")


def test_shear_end_shifts_bottom_band() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 200.0)
    band = 50.0
    angle = 20.0
    out = shear_end(stem, (ctx.stem / 2.0, 0.0), angle, band=band, along="y")
    shift = band * math.tan(math.radians(angle))
    bottom = [
        p.x
        for c in out.contours
        for seg in c.segments
        for p in seg.points
        if abs(p.y) < 1e-6
    ]
    assert min(bottom) == pytest.approx(shift, abs=0.05)
    assert max(bottom) == pytest.approx(ctx.stem + shift, abs=0.05)
    # Top unchanged
    top = [
        p.x
        for c in out.contours
        for seg in c.segments
        for p in seg.points
        if abs(p.y - 200.0) < 1e-6
    ]
    assert min(top) == pytest.approx(0.0, abs=0.05)
    assert max(top) == pytest.approx(ctx.stem, abs=0.05)


def test_shear_end_zero_angle_is_identity() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 100.0)
    assert shear_end(stem, (10.0, 0.0), 0.0) is stem


@pytestmark_bool
def test_flat_end_cuts_stem() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 200.0)
    stub = flat_end(stem, (ctx.stem / 2.0, 40.0), angle_deg=0.0, keep="positive")
    _min_x, min_y, _max_x, max_y = bounds(stub)
    assert max_y == pytest.approx(40.0, abs=2.0)
    assert min_y == pytest.approx(0.0, abs=0.5)
    assert stub.contour_count >= 1


@pytestmark_bool
def test_ball_end_extends_bounds() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 100.0)
    r = 25.0
    out = ball_end(stem, (ctx.stem / 2.0, 0.0), radius=r)
    min_x, min_y, max_x, max_y = bounds(out)
    assert min_y == pytest.approx(-r, abs=0.5)
    assert max_y >= 100.0 - 0.5
    assert max_x - min_x >= ctx.stem - 0.5


@pytestmark_bool
def test_hook_end_adds_geometry() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 120.0)
    out = hook_end(
        stem,
        (ctx.stem / 2.0, 0.0),
        radius=ctx.stem * 2.0,
        width=ctx.stem,
        sweep_deg=150.0,
        start_deg=200.0,
    )
    assert out.contour_count >= 1
    bb = bounds(out)
    assert bb[2] - bb[0] > ctx.stem
    assert bb[3] - bb[1] > 120.0


@pytestmark_bool
def test_open_counter_right_on_bowl_ring() -> None:
    ctx = DesignContext.geometric_sans()
    outer, hole = bowl(ctx, 100.0, 100.0, rx=80.0, ry=70.0)
    opened = open_bowl_ring(outer, hole, "right", 0.60, ctx)
    assert opened.contour_count >= 1
    # Bite should cut into the right flank — max_x shrinks vs solid outer
    assert bounds(opened)[2] < bounds(outer)[2] - 1.0


@pytestmark_bool
def test_open_counter_amount_scales_gap() -> None:
    ctx = DesignContext.geometric_sans()
    outer, hole = bowl(ctx, 0.0, 0.0, rx=100.0, ry=90.0)
    narrow = open_bowl_ring(outer, hole, "right", 0.30, ctx)
    wide = open_bowl_ring(outer, hole, "right", 0.70, ctx)
    # Wider aperture removes more of the right side
    assert bounds(wide)[2] <= bounds(narrow)[2] + 0.5


def test_open_counter_rejects_non_positive() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 50.0)
    with pytest.raises(ValueError):
        open_counter(stem, "right", 0.0, ctx)
