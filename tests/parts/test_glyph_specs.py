"""TK-303: typed weak-glyph specs and Controls.tuned_glyph."""

from __future__ import annotations

import pytest

from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import Controls, DesignContext
from typekernel.parts.glyph_specs import WEAK_GLYPH_SPECS, FSpec, TSpec, merge_spec
from typekernel.qa.outline_hash import composed_glyph_hash


@pytest.mark.parametrize("ch", ("f", "t", "j", "a", "e", "s"))
def test_tuned_glyph_defaults_match_stock_derivation(ch: str) -> None:
    ctx = DesignContext.humanist_sans()
    base = Controls.from_context(ctx).build(ch)
    tuned = Controls.from_context(ctx).tuned_glyph(ch).build(ch)
    assert composed_glyph_hash(base) == composed_glyph_hash(tuned)


def test_cap_glyph_specs_default_match_stock() -> None:
    ctx = DesignContext.humanist_sans()
    base = Controls.from_context(ctx).build_all("GKRY")
    tuned = (
        Controls.from_context(ctx)
        .tuned_glyph("G")
        .tuned_glyph("K")
        .tuned_glyph("R")
        .tuned_glyph("Y")
        .build_all("GKRY")
    )
    for ch in "GKRY":
        assert composed_glyph_hash(base[ch]) == composed_glyph_hash(tuned[ch])


def test_tuned_glyph_defaults_preserve_supported_charset_hashes() -> None:
    ctx = DesignContext.humanist_sans()
    base = Controls.from_context(ctx)
    tuned = Controls.from_context(ctx)
    for ch in sorted(WEAK_GLYPH_SPECS):
        tuned = tuned.tuned_glyph(ch)
    chars = base.supported
    base_glyphs = base.build_all(chars)
    tuned_glyphs = tuned.build_all(chars)
    mismatches = [
        ch
        for ch in chars
        if composed_glyph_hash(base_glyphs[ch]) != composed_glyph_hash(tuned_glyphs[ch])
    ]
    assert mismatches == []


def test_cap_vwx_mn_specs_default_match_stock() -> None:
    ctx = DesignContext.humanist_sans()
    chars = "VWXMN"
    base = Controls.from_context(ctx).build_all(chars)
    tuned = Controls.from_context(ctx)
    for ch in chars:
        tuned = tuned.tuned_glyph(ch)
    built = tuned.build_all(chars)
    for ch in chars:
        assert composed_glyph_hash(base[ch]) == composed_glyph_hash(built[ch])


def test_k_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = Controls.from_context(ctx).tuned_glyph("K", width=0.86).build("K")
    wide = Controls.from_context(ctx).tuned_glyph("K", width=0.98).build("K")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_v_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = Controls.from_context(ctx).tuned_glyph("V", width=0.88).build("V")
    wide = Controls.from_context(ctx).tuned_glyph("V", width=1.06).build("V")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_g_bar_reach_moves_crossbar() -> None:
    ctx = DesignContext.humanist_sans()
    short = Controls.from_context(ctx).tuned_glyph("G", bar_reach=0.05).build("G")
    long = Controls.from_context(ctx).tuned_glyph("G", bar_reach=0.18).build("G")
    assert composed_glyph_hash(short) != composed_glyph_hash(long)


def test_cap_a_bar_moves_crossbar() -> None:
    ctx = DesignContext.humanist_sans()
    low = Controls.from_context(ctx).tuned_glyph("A", bar=0.22).build("A")
    high = Controls.from_context(ctx).tuned_glyph("A", bar=0.34).build("A")
    assert composed_glyph_hash(low) != composed_glyph_hash(high)


def test_y_junction_moves_crotch() -> None:
    ctx = DesignContext.humanist_sans()
    low = Controls.from_context(ctx).tuned_glyph("Y", junction=0.34).build("Y")
    high = Controls.from_context(ctx).tuned_glyph("Y", junction=0.52).build("Y")
    assert composed_glyph_hash(low) != composed_glyph_hash(high)


def test_t_arm_monotone_moves_terminal() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = Controls.from_context(ctx).tuned_glyph("t", arm=0.45).build("t")
    wide = Controls.from_context(ctx).tuned_glyph("t", arm=0.72).build("t")
    _, _, x_n, _ = bounds(narrow.solids[0])
    _, _, x_w, _ = bounds(wide.solids[0])
    assert x_w > x_n + 2.0


def test_f_arm_monotone_moves_terminal() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = Controls.from_context(ctx).tuned_glyph("f", arm=0.55).build("f")
    wide = Controls.from_context(ctx).tuned_glyph("f", arm=0.88).build("f")
    _, _, x_n, _ = bounds(narrow.solids[0])
    _, _, x_w, _ = bounds(wide.solids[0])
    assert x_w > x_n + 2.0


def test_e_bar_raise_changes_outline() -> None:
    ctx = DesignContext.humanist_sans()
    low = Controls.from_context(ctx).tuned_glyph("e", bar_raise=-0.2).build("e")
    high = Controls.from_context(ctx).tuned_glyph("e", bar_raise=0.35).build("e")
    assert composed_glyph_hash(low) != composed_glyph_hash(high)


def test_s_spine_monotone_moves_midline() -> None:
    ctx = DesignContext.humanist_sans()
    low = Controls.from_context(ctx).tuned_glyph("s", spine=0.42).build("s")
    high = Controls.from_context(ctx).tuned_glyph("s", spine=0.58).build("s")
    y = ctx.x_height * 0.5
    runs_lo = ink_intervals_at_y(list(low.solids), y)
    runs_hi = ink_intervals_at_y(list(high.solids), y)
    assert runs_lo and runs_hi
    assert runs_hi[0] != runs_lo[0]


def test_merge_spec_rejects_unknown_fields() -> None:
    with pytest.raises(TypeError, match="no field"):
        merge_spec("t", TSpec(), foo=1.0)


def test_tuned_glyph_l0_counts_toward_design_review() -> None:
    from typekernel.qa.design_review import design_review

    controls = (
        Controls.from_context(DesignContext.humanist_sans())
        .tuned_glyph("f", arm=0.8)
        .tuned_glyph("t", arm=0.55)
    )
    review = design_review(controls)
    assert review.l0_gaps == ()
    assert any("spec f:" in note for note in review.notes)
    assert FSpec(arm=0.8) == controls.glyph_specs["f"]
