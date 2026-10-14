"""TK-303: typed weak-glyph specs and Controls.tuned_glyph."""

from __future__ import annotations

import pytest

from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import Controls, DesignContext
from typekernel.parts.glyph_specs import FSpec, TSpec, merge_spec
from typekernel.qa.outline_hash import composed_glyph_hash


def test_tuned_glyph_defaults_match_stock_derivation() -> None:
    ctx = DesignContext.code_clear()
    base = Controls.from_context(ctx).build_all("ft")
    tuned = Controls.from_context(ctx).tuned_glyph("f").tuned_glyph("t").build_all("ft")
    for ch in "ft":
        assert composed_glyph_hash(base[ch]) == composed_glyph_hash(tuned[ch])


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
