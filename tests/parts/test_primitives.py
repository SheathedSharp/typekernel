"""Tests for glyph part factories."""

from __future__ import annotations

import pytest

from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    bowl,
    diagonal_stem,
    hook_terminal,
    horizontal_bar,
    tittle,
    u_bowl,
    vertical_stem,
)


def test_vertical_stem_size() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 10.0, 0.0, ctx.x_height)
    min_x, min_y, max_x, max_y = bounds(stem)
    assert max_x - min_x == pytest.approx(ctx.stem)
    assert max_y - min_y == pytest.approx(ctx.x_height)


def test_horizontal_bar_uses_thin() -> None:
    ctx = DesignContext(stem=80.0, contrast=0.5)
    bar = horizontal_bar(ctx, 0.0, 200.0, 100.0)
    _, min_y, _, max_y = bounds(bar)
    assert max_y - min_y == pytest.approx(ctx.thin)


def test_bowl_returns_outer_and_counter() -> None:
    ctx = DesignContext.geometric_sans()
    outer, hole = bowl(ctx, 100.0, 100.0, rx=80.0, ry=80.0)
    assert outer.contour_count == 1
    assert hole.contour_count == 1
    o = bounds(outer)
    h = bounds(hole)
    assert (o[2] - o[0]) > (h[2] - h[0])


def test_diagonal_stem_has_positive_area_box() -> None:
    ctx = DesignContext.geometric_sans()
    d = diagonal_stem(ctx, 0.0, 100.0, 80.0, 0.0)
    min_x, min_y, max_x, max_y = bounds(d)
    assert max_x > min_x
    assert max_y > min_y


def test_hook_and_tittle() -> None:
    ctx = DesignContext.geometric_sans()
    hook = hook_terminal(ctx, 40.0, ctx.x_height, ctx.descender)
    dot = tittle(ctx, 40.0, ctx.x_height + 20.0)
    assert hook.contour_count == 1
    assert dot.contour_count == 1


def test_u_bowl_closed() -> None:
    ctx = DesignContext.geometric_sans()
    u = u_bowl(ctx, 0.0, 300.0, ctx.x_height, -ctx.overshoot)
    assert u.contours[0].closed
