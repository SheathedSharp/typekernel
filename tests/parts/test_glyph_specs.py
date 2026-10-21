"""TK-303: typed weak-glyph specs and FormSources.tuned_glyph."""

from __future__ import annotations

import pytest

from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import DesignContext, FormSources
from typekernel.parts.glyph_specs import WEAK_GLYPH_SPECS, FSpec, TSpec, merge_spec
from typekernel.qa.outline_hash import composed_glyph_hash


@pytest.mark.parametrize("ch", ("f", "t", "j", "a", "e", "s"))
def test_tuned_glyph_defaults_match_stock_derivation(ch: str) -> None:
    ctx = DesignContext.humanist_sans()
    base = FormSources.from_context(ctx).derive_one(ch)
    tuned = FormSources.from_context(ctx).tuned_glyph(ch).derive_one(ch)
    assert composed_glyph_hash(base) == composed_glyph_hash(tuned)


def test_cap_glyph_specs_default_match_stock() -> None:
    ctx = DesignContext.humanist_sans()
    base = FormSources.from_context(ctx).derive("GKRY")
    tuned = (
        FormSources.from_context(ctx)
        .tuned_glyph("G")
        .tuned_glyph("K")
        .tuned_glyph("R")
        .tuned_glyph("Y")
        .derive("GKRY")
    )
    for ch in "GKRY":
        assert composed_glyph_hash(base[ch]) == composed_glyph_hash(tuned[ch])


def test_tuned_glyph_defaults_preserve_supported_charset_hashes() -> None:
    ctx = DesignContext.humanist_sans()
    base = FormSources.from_context(ctx)
    tuned = FormSources.from_context(ctx)
    for ch in sorted(WEAK_GLYPH_SPECS):
        tuned = tuned.tuned_glyph(ch)
    chars = base.supported
    base_glyphs = base.derive(chars)
    tuned_glyphs = tuned.derive(chars)
    mismatches = [
        ch
        for ch in chars
        if composed_glyph_hash(base_glyphs[ch]) != composed_glyph_hash(tuned_glyphs[ch])
    ]
    assert mismatches == []


def test_cap_vwx_mn_specs_default_match_stock() -> None:
    ctx = DesignContext.humanist_sans()
    chars = "VWXMN"
    base = FormSources.from_context(ctx).derive(chars)
    tuned = FormSources.from_context(ctx)
    for ch in chars:
        tuned = tuned.tuned_glyph(ch)
    built = tuned.derive(chars)
    for ch in chars:
        assert composed_glyph_hash(base[ch]) == composed_glyph_hash(built[ch])


def test_k_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("K", width=0.86).derive_one("K")
    wide = FormSources.from_context(ctx).tuned_glyph("K", width=0.98).derive_one("K")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_b_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("B", width=0.86).derive_one("B")
    wide = FormSources.from_context(ctx).tuned_glyph("B", width=0.98).derive_one("B")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_u_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("U", width=0.88).derive_one("U")
    wide = FormSources.from_context(ctx).tuned_glyph("U", width=1.04).derive_one("U")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_q_tail_reach_monotone_moves_tip() -> None:
    ctx = DesignContext.humanist_sans()
    short = FormSources.from_context(ctx).tuned_glyph("Q", tail_reach=0.92).derive_one("Q")
    long = FormSources.from_context(ctx).tuned_glyph("Q", tail_reach=1.08).derive_one("Q")
    assert composed_glyph_hash(short) != composed_glyph_hash(long)


def test_cap_s_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("S", width=0.78).derive_one("S")
    wide = FormSources.from_context(ctx).tuned_glyph("S", width=0.94).derive_one("S")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_d_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("D", width=0.98).derive_one("D")
    wide = FormSources.from_context(ctx).tuned_glyph("D", width=1.12).derive_one("D")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_cap_e_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("E", width=0.76).derive_one("E")
    wide = FormSources.from_context(ctx).tuned_glyph("E", width=0.92).derive_one("E")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_cap_t_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("T", width=0.84).derive_one("T")
    wide = FormSources.from_context(ctx).tuned_glyph("T", width=1.0).derive_one("T")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_v_width_monotone_opens_outline() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("V", width=0.88).derive_one("V")
    wide = FormSources.from_context(ctx).tuned_glyph("V", width=1.06).derive_one("V")
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_g_bar_reach_moves_crossbar() -> None:
    ctx = DesignContext.humanist_sans()
    short = FormSources.from_context(ctx).tuned_glyph("G", bar_reach=0.05).derive_one("G")
    long = FormSources.from_context(ctx).tuned_glyph("G", bar_reach=0.18).derive_one("G")
    assert composed_glyph_hash(short) != composed_glyph_hash(long)


def test_cap_a_bar_moves_crossbar() -> None:
    ctx = DesignContext.humanist_sans()
    low = FormSources.from_context(ctx).tuned_glyph("A", bar=0.22).derive_one("A")
    high = FormSources.from_context(ctx).tuned_glyph("A", bar=0.34).derive_one("A")
    assert composed_glyph_hash(low) != composed_glyph_hash(high)


def test_y_junction_moves_crotch() -> None:
    ctx = DesignContext.humanist_sans()
    low = FormSources.from_context(ctx).tuned_glyph("Y", junction=0.34).derive_one("Y")
    high = FormSources.from_context(ctx).tuned_glyph("Y", junction=0.52).derive_one("Y")
    assert composed_glyph_hash(low) != composed_glyph_hash(high)


def test_t_arm_monotone_moves_terminal() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("t", arm=0.45).derive_one("t")
    wide = FormSources.from_context(ctx).tuned_glyph("t", arm=0.72).derive_one("t")
    _, _, x_n, _ = bounds(narrow.solids[0])
    _, _, x_w, _ = bounds(wide.solids[0])
    assert x_w > x_n + 2.0


def test_f_arm_monotone_moves_terminal() -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph("f", arm=0.55).derive_one("f")
    wide = FormSources.from_context(ctx).tuned_glyph("f", arm=0.88).derive_one("f")
    _, _, x_n, _ = bounds(narrow.solids[0])
    _, _, x_w, _ = bounds(wide.solids[0])
    assert x_w > x_n + 2.0


def test_e_bar_raise_changes_outline() -> None:
    ctx = DesignContext.humanist_sans()
    low = FormSources.from_context(ctx).tuned_glyph("e", bar_raise=-0.2).derive_one("e")
    high = FormSources.from_context(ctx).tuned_glyph("e", bar_raise=0.35).derive_one("e")
    assert composed_glyph_hash(low) != composed_glyph_hash(high)


def test_s_spine_monotone_moves_midline() -> None:
    ctx = DesignContext.humanist_sans()
    low = FormSources.from_context(ctx).tuned_glyph("s", spine=0.42).derive_one("s")
    high = FormSources.from_context(ctx).tuned_glyph("s", spine=0.58).derive_one("s")
    y = ctx.x_height * 0.5
    runs_lo = ink_intervals_at_y(list(low.solids), y)
    runs_hi = ink_intervals_at_y(list(high.solids), y)
    assert runs_lo and runs_hi
    assert runs_hi[0] != runs_lo[0]


@pytest.mark.parametrize(
    ("ch", "low", "high"),
    (
        ("F", 0.74, 0.90),
        ("J", 0.66, 0.78),
        ("L", 0.70, 0.86),
        ("M", 1.10, 1.26),
        ("N", 0.92, 1.08),
        ("P", 0.84, 0.96),
        ("R", 0.86, 1.02),
        ("W", 1.30, 1.50),
        ("X", 0.84, 1.00),
        ("Y", 0.90, 1.06),
        ("Z", 0.80, 0.96),
        ("s", 0.74, 0.90),
    ),
)
def test_width_spec_monotone_changes_outline(ch: str, low: float, high: float) -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph(ch, width=low).derive_one(ch)
    wide = FormSources.from_context(ctx).tuned_glyph(ch, width=high).derive_one(ch)
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


@pytest.mark.parametrize(
    ("ch", "field", "low", "high"),
    (
        ("A", "width", 0.92, 1.12),
        ("A", "apex", 0.22, 0.48),
        ("a", "join", 0.70, 0.95),
        ("B", "top_scale", 0.82, 0.98),
        ("B", "straight", 0.35, 0.55),
        ("B", "waist", 0.45, 0.62),
        ("C", "aperture", 0.85, 1.15),
        ("D", "straight", 0.30, 0.55),
        ("e", "aperture", 0.85, 1.15),
        ("j", "arm", 0.55, 0.95),
        ("J", "hook", 0.40, 0.70),
        ("J", "spring", 0.30, 0.46),
        ("K", "vertex", 0.36, 0.52),
        ("P", "straight", 0.35, 0.55),
        ("P", "bowl", 0.40, 0.54),
        ("Q", "tail_drop", 0.06, 0.14),
        ("R", "straight", 0.35, 0.55),
        ("R", "leg_at", 0.22, 0.38),
        ("s", "aperture", 0.85, 1.15),
        ("s", "top_scale", 0.82, 0.98),
        ("t", "rise", 0.15, 0.45),
        ("U", "spring", 0.30, 0.46),
    ),
)
def test_glyph_spec_field_monotone_changes_outline(
    ch: str, field: str, low: float, high: float
) -> None:
    ctx = DesignContext.humanist_sans()
    narrow = FormSources.from_context(ctx).tuned_glyph(ch, **{field: low}).derive_one(ch)
    wide = FormSources.from_context(ctx).tuned_glyph(ch, **{field: high}).derive_one(ch)
    assert composed_glyph_hash(narrow) != composed_glyph_hash(wide)


def test_m_apex_monotone_moves_baseline_vertex() -> None:
    """``MSpec.apex`` is ladder-overridden on light stems (see ``M_from_H``)."""
    ctx = DesignContext.humanist_sans().tuned(stem=150.0)
    low = FormSources.from_context(ctx).tuned_glyph("M", apex=0.30).derive_one("M")
    high = FormSources.from_context(ctx).tuned_glyph("M", apex=0.48).derive_one("M")
    assert composed_glyph_hash(low) != composed_glyph_hash(high)


def test_merge_spec_rejects_unknown_fields() -> None:
    with pytest.raises(TypeError, match="no field"):
        merge_spec("t", TSpec(), foo=1.0)


def test_tuned_glyph_l0_counts_toward_design_review() -> None:
    from typekernel.qa.design_review import design_review

    controls = (
        FormSources.from_context(DesignContext.humanist_sans())
        .tuned_glyph("f", arm=0.8)
        .tuned_glyph("t", arm=0.55)
    )
    review = design_review(controls)
    assert review.l0_gaps == ()
    assert any("spec f:" in note for note in review.notes)
    assert FSpec(arm=0.8) == controls.glyph_specs["f"]
