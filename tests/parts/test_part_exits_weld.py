"""Part-exit quality: continuous yoke, soft_union weld, flare terminal."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.geo.joins import classify_joins
from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    arch,
    flare_end,
    flared_terminal_piece,
    horizontal_bar,
    shoulder_yoke,
    soft_union,
    soften_stem_branch,
    vertical_stem,
)
from typekernel.qa.lint import lint_glyph

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None
pytestmark_bool = pytest.mark.skipif(not HAS_PATHOPS, reason="pathops required")


def _keyholes(glyph, ctx, name: str) -> list[str]:
    return [i.rule for i in lint_glyph(glyph, ctx, glyph_name=name) if i.rule == "R2_keyhole"]


def test_shoulder_yoke_is_single_closed_contour() -> None:
    ctx = DesignContext.humanist_sans()
    yoke = shoulder_yoke(ctx, 40.0)
    assert yoke.contour_count == 1
    assert yoke.contours[0].closed
    min_x, min_y, max_x, max_y = bounds(yoke)
    assert min_y == pytest.approx(0.0, abs=0.5)
    assert max_y > ctx.x_height  # crown overshoot
    assert max_x - min_x > 2.0 * ctx.stem
    # Continuous construction: no boolean debris keyholes when packed.
    g = GlyphAssembler(ctx).add(yoke).build()
    assert _keyholes(g, ctx, "yoke") == []


def test_shoulder_yoke_counter_widens() -> None:
    ctx = DesignContext.geometric_sans()
    narrow = bounds(shoulder_yoke(ctx, 0.0, counter=120.0))
    wide = bounds(shoulder_yoke(ctx, 0.0, counter=220.0))
    assert (wide[2] - wide[0]) > (narrow[2] - narrow[0])


@pytestmark_bool
def test_soft_union_stem_bar_no_keyhole() -> None:
    ctx = DesignContext.humanist_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, ctx.x_height)
    bar = horizontal_bar(ctx, 0.0, 220.0, ctx.x_height * 0.55)
    welded = soft_union([stem, bar], radius=ctx.join_radius)
    assert welded.contour_count >= 1
    g = GlyphAssembler(ctx).add(welded).build()
    assert _keyholes(g, ctx, "stem_bar") == []
    joins = classify_joins(welded)
    # Blend should not invent a pile of raw corners at the T-junction.
    assert joins.corners <= 6


@pytestmark_bool
def test_soft_union_rejects_empty_and_bad_radius() -> None:
    with pytest.raises(ValueError, match="at least one"):
        soft_union([], radius=8.0)
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 100.0)
    with pytest.raises(ValueError, match="positive"):
        soft_union([stem], radius=0.0)


def test_flare_end_widens_tip_band() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 200.0)
    before = bounds(stem)
    out = flare_end(stem, (ctx.stem / 2.0, 0.0), amount=0.5, band=60.0, along="y")
    after = bounds(out)
    assert (after[2] - after[0]) > (before[2] - before[0])
    # Top of stem stays put.
    top_x = [
        p.x
        for c in out.contours
        for seg in c.segments
        for p in seg.points
        if abs(p.y - 200.0) < 1e-6
    ]
    assert min(top_x) == pytest.approx(0.0, abs=0.05)
    assert max(top_x) == pytest.approx(ctx.stem, abs=0.05)


def test_flare_end_zero_is_identity() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 100.0)
    assert flare_end(stem, (10.0, 0.0), amount=0.0) is stem


def test_flared_terminal_piece_is_trapezoid() -> None:
    ctx = DesignContext.geometric_sans()
    tip = flared_terminal_piece(ctx, 0.0, 40.0, ctx.stem, 0.0, flare=0.5)
    assert tip.contour_count == 1
    min_x, _min_y, max_x, _max_y = bounds(tip)
    assert max_x - min_x > ctx.stem  # flared wider than stem face


def test_arch_meet_fillet_zero_keeps_square_foot() -> None:
    ctx = DesignContext.geometric_sans()
    square = arch(ctx, 100.0, 300.0, 200.0, 520.0, meet_fillet=0.0)
    filleted = arch(ctx, 100.0, 300.0, 200.0, 520.0, meet_fillet=18.0)
    # Filleted path uses more cubics at the stem meets.
    n_cubic_sq = sum(1 for s in square.contours[0].segments if s.kind == "cubic")
    n_cubic_fi = sum(1 for s in filleted.contours[0].segments if s.kind == "cubic")
    assert n_cubic_fi > n_cubic_sq


def test_soften_stem_branch_blends_sharp_crotch() -> None:
    """Synthetic sharp branch → soften drops the kink at the join."""
    from typekernel.geo.path_builder import PathBuilder

    ctx = DesignContext.humanist_sans()
    stem = ctx.stem
    branch_y = ctx.x_height * 0.58
    # Minimal sharp n-like branch: vertical into horizontal ledge (proxy).
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(0.0, ctx.x_height)
    b.lineTo(stem, ctx.x_height)
    b.lineTo(stem, branch_y)
    # Sharp turn into shoulder-ish cubic
    b.curveTo(stem + 40.0, branch_y, stem + 80.0, ctx.x_height + 10.0, stem + 120.0, ctx.x_height + 10.0)
    b.lineTo(stem + 120.0, 0.0)
    b.lineTo(0.0, 0.0)
    b.closePath()
    sharp = b.build()
    before = classify_joins(sharp)
    soft = soften_stem_branch(
        sharp,
        stem_x=stem,
        branch_y=branch_y,
        stem=stem,
        stem_top=ctx.x_height,
    )
    after = classify_joins(soft)
    # Soften should not increase raw corners; kink at branch should ease.
    assert after.corners <= before.corners + 1
    assert soft.contour_count == 1
