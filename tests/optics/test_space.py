"""Optical whitespace spacing."""

from __future__ import annotations

from typekernel.optics.space import (
    fit_kern_pair,
    pair_gap_bbox,
    pair_gap_optical,
    space_word_optical,
    suggest_sidebearings_optical,
)
from typekernel.parts import DesignContext, word_zayju


def test_suggest_sidebearings_optical_asymmetric_for_open_shapes() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = word_zayju(ctx)
    # y has a diagonal left flank → left inset large → smaller LSB than a boxed stem.
    y_lsb, y_rsb = suggest_sidebearings_optical(glyphs[2], ctx)  # y
    j_lsb, j_rsb = suggest_sidebearings_optical(glyphs[3], ctx)  # j
    assert y_lsb > 0 and y_rsb > 0
    assert j_lsb > 0 and j_rsb > 0


def test_pair_gap_optical_positive_for_spaced_word() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = word_zayju(ctx)
    gap = pair_gap_optical(glyphs[0], glyphs[1], kern=0.0)
    bbox = pair_gap_bbox(glyphs[0], glyphs[1], kern=0.0)
    assert gap > 0
    assert bbox > 0


def test_fit_kern_pair_moves_toward_target() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = word_zayju(ctx)
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
    base = word_zayju(ctx)
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
