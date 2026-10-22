"""Part-exit tests: italic stroke parts, double_shoulder_yoke, apply_flare_terminal."""

from __future__ import annotations

import pytest

from typekernel.geo.joins import classify_joins
from typekernel.geo.outline import bounds
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    apply_flare_terminal,
    double_shoulder_yoke,
    emit_italic_entry_kick,
    emit_italic_exit_outstroke,
    italic_entry_kick,
    italic_exit_outstroke,
    italic_kick_dims,
    italic_written_stem,
    vertical_stem,
)
from typekernel.parts.terminal_openings import apply_terminal_shear
from typekernel.qa.lint import lint_glyph


def _keyholes(glyph, ctx, name: str) -> list[str]:
    return [i.rule for i in lint_glyph(glyph, ctx, glyph_name=name) if i.rule == "R2_keyhole"]


def test_italic_kick_dims_scale_with_stem() -> None:
    dx0, dy0 = italic_kick_dims(40.0)
    dx1, dy1 = italic_kick_dims(120.0)
    assert dx1 > dx0
    assert dy1 > dy0


def test_italic_entry_kick_closed_no_keyhole() -> None:
    ctx = DesignContext.humanist_sans()
    part = italic_entry_kick(ctx, 10.0)
    assert part.contour_count == 1
    assert part.contours[0].closed
    g = GlyphAssembler(ctx).add(part).build()
    assert _keyholes(g, ctx, "entry_kick") == []
    min_x, min_y, max_x, max_y = bounds(part)
    assert min_y == pytest.approx(0.0, abs=0.5)
    assert max_y == pytest.approx(ctx.x_height, abs=0.5)
    assert max_x - min_x == pytest.approx(ctx.stem, abs=0.5)


def test_italic_exit_outstroke_closed_no_keyhole() -> None:
    ctx = DesignContext.geometric_sans()
    part = italic_exit_outstroke(ctx, 0.0, ctx.stem)
    assert part.contour_count == 1
    g = GlyphAssembler(ctx).add(part).build()
    assert _keyholes(g, ctx, "exit") == []


def test_italic_written_stem_has_kick_and_outstroke() -> None:
    ctx = DesignContext.humanist_sans()
    stem = italic_written_stem(ctx)
    assert stem.contour_count == 1
    # Baseline should not be a sharp rectangle: kick/outstroke pull corners in.
    bottom = [
        p.x
        for c in stem.contours
        for seg in c.segments
        for p in seg.points
        if abs(p.y) < 1e-6
    ]
    assert min(bottom) > 0.0  # entry kick inset
    assert max(bottom) < ctx.stem  # exit outstroke inset
    g = GlyphAssembler(ctx).add(stem).build()
    assert _keyholes(g, ctx, "written_stem") == []


def test_emit_helpers_build_continuous_path() -> None:
    ctx = DesignContext.humanist_sans()
    t = ctx.stem
    b = PathBuilder()
    emit_italic_entry_kick(b, 0.0, stem=t, left_top=ctx.x_height)
    b.lineTo(t, ctx.x_height)
    emit_italic_exit_outstroke(b, 0.0, t, stem=t)
    b.closePath()
    out = b.build()
    assert out.contour_count == 1
    assert out.contours[0].closed


def test_double_shoulder_yoke_single_contour_no_keyhole() -> None:
    ctx = DesignContext.humanist_sans()
    yoke = double_shoulder_yoke(ctx, 40.0)
    assert yoke.contour_count == 1
    assert yoke.contours[0].closed
    g = GlyphAssembler(ctx).add(yoke).build()
    assert _keyholes(g, ctx, "m_yoke") == []
    joins = classify_joins(yoke)
    # Continuous construction — not a pile of raw boolean corners.
    assert joins.corners <= 8
    min_x, min_y, max_x, max_y = bounds(yoke)
    assert min_y == pytest.approx(0.0, abs=0.5)
    assert max_y > ctx.x_height
    assert max_x - min_x > 3.0 * ctx.stem  # three stems


def test_double_shoulder_yoke_counter_scale_narrows() -> None:
    ctx = DesignContext.geometric_sans()
    wide = bounds(double_shoulder_yoke(ctx, 0.0, counter_scale=1.0))
    narrow = bounds(double_shoulder_yoke(ctx, 0.0, counter_scale=0.8))
    assert (wide[2] - wide[0]) > (narrow[2] - narrow[0])


def test_apply_flare_terminal_widens_opt_in() -> None:
    ctx = DesignContext.geometric_sans().tuned(terminal_style="vertical")
    stem = vertical_stem(ctx, 0.0, 0.0, 200.0)
    before = bounds(stem)[2] - bounds(stem)[0]
    out = apply_flare_terminal(ctx, stem, at=(ctx.stem / 2.0, 0.0), amount=0.45)
    after = bounds(out)[2] - bounds(out)[0]
    assert after > before


def test_stock_flared_style_still_uses_shear_not_flare() -> None:
    """Regression: stock terminal_style=flared must not silently switch to flare_end."""
    ctx = DesignContext.geometric_sans().tuned(terminal_style="flared")
    stem = vertical_stem(ctx, 0.0, 0.0, 200.0)
    # apply_terminal_shear on flared uses shear_end (+angle), which shifts x
    # but does not symmetrically widen like flare_end.
    sheared = apply_terminal_shear(ctx, stem, at=(ctx.stem / 2.0, 0.0), along="y", inward="-")
    flared = apply_flare_terminal(ctx, stem, at=(ctx.stem / 2.0, 0.0), amount=0.4)
    # Distinct recipes: shear shifts, flare widens — bounds differ.
    assert bounds(sheared) != bounds(flared)
