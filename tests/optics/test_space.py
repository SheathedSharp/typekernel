"""Optical whitespace spacing."""

from __future__ import annotations

from typekernel.optics.space import (
    fit_kern_pair,
    pair_gap_bbox,
    pair_gap_optical,
    space_font,
    space_word_optical,
    suggest_sidebearings_optical,
)
from typekernel.parts import DesignContext, FormSources


def _zayju(ctx: DesignContext):
    drawn = FormSources.from_context(ctx).derive("zayju")
    return [drawn[ch] for ch in "zayju"]


def test_suggest_sidebearings_optical_asymmetric_for_open_shapes() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = _zayju(ctx)
    # y has a diagonal left flank → left inset large → smaller LSB than a boxed stem.
    y_lsb, y_rsb = suggest_sidebearings_optical(glyphs[2], ctx)  # y
    j_lsb, j_rsb = suggest_sidebearings_optical(glyphs[3], ctx)  # j
    assert y_lsb > 0 and y_rsb > 0
    assert j_lsb > 0 and j_rsb > 0


def test_pair_gap_optical_positive_for_spaced_word() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = _zayju(ctx)
    gap = pair_gap_optical(glyphs[0], glyphs[1], kern=0.0)
    bbox = pair_gap_bbox(glyphs[0], glyphs[1], kern=0.0)
    assert gap > 0
    assert bbox > 0


def test_fit_kern_pair_moves_toward_target() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = _zayju(ctx)
    left, right = glyphs[0], glyphs[1]
    at0 = pair_gap_optical(left, right, kern=0.0)
    target = at0 * 0.7
    k = fit_kern_pair(left, right, target)
    after = pair_gap_optical(left, right, kern=k)
    assert abs(after - target) < abs(at0 - target)
    assert abs(after - target) < 2.0


def test_space_word_optical_evens_optical_gaps() -> None:
    ctx = DesignContext.geometric_sans()
    names = list("zayju")
    base = _zayju(ctx)
    before = [
        pair_gap_optical(base[i], base[i + 1], kern=0.0) for i in range(4)
    ]
    result = space_word_optical(base, names)
    after = [
        pair_gap_optical(
            result.glyphs[i],
            result.glyphs[i + 1],
            kern=result.kerning.lookup(names[i], names[i + 1]),
        )
        for i in range(4)
    ]
    before_ratio = max(before) / min(before)
    after_ratio = max(after) / min(after)
    assert after_ratio < before_ratio
    assert after_ratio <= 1.15


def test_space_font_tabs_figures_and_sets_sidebearings() -> None:
    ctx = DesignContext.code_clear()
    drawn = FormSources.from_context(ctx).derive("no012")
    spaced = space_font(drawn, ctx)
    assert spaced["n"].advance > drawn["n"].advance * 0.5
    assert spaced["0"].advance == spaced["1"].advance


def test_space_font_flat_stem_gap_tracks_rhythm() -> None:
    """Flat-stem pairs after ``space_font`` land near ``rhythm.target_gap``."""
    from typekernel.parts.metrics import rhythm_from_control_glyphs

    ctx = DesignContext.code_clear()
    drawn = FormSources.from_context(ctx).derive("nao")
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    gap = pair_gap_optical(spaced["n"], spaced["a"], kern=0.0)
    assert abs(gap - rhythm.target_gap) <= 2.0
