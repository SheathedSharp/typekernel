"""DesignSequence — first-class designer-order unlock gate."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.qa.design_sequence import (
    DesignSequence,
    DesignSequenceError,
    default_body_design_order,
)
from typekernel.qa.style_consistency import StyleConsistencyTolerances


def _loose() -> StyleConsistencyTolerances:
    return StyleConsistencyTolerances(
        stem_median=40.0,
        contrast_ratio=10.0,
        entry_rail_y=600.0,
        exit_rail_y=600.0,
        exit_slant_deg=180.0,
        bowl_center_y=300.0,
        ink_ymin=300.0,
        ink_ymax=500.0,
    )


def test_start_unlocks_control_only() -> None:
    c = Controls.from_context(DesignContext.geometric_sans())
    seq = DesignSequence.start("n", c.build("n"), planned_order=("n", "o", "h"))
    assert seq.unlocked == ("n",)
    assert seq.next_planned() == "o"
    assert not seq.is_complete


def test_try_add_unlocks_on_pass() -> None:
    c = Controls.from_context(DesignContext.geometric_sans())
    seq = DesignSequence.from_controls(
        c, control="n", order=("n", "o", "h"), tolerances=_loose()
    )
    rep = seq.try_add("o", c.build("o"))
    assert rep.passed
    assert "o" in seq.unlocked
    seq.add("h", c.build("h"))
    assert seq.is_complete
    glyphs = seq.export_glyphs(require_complete=True)
    assert set(glyphs) == {"n", "o", "h"}


def test_try_add_refuses_without_unlocking() -> None:
    c = Controls.from_context(DesignContext.geometric_sans())
    # Propose a thinner master's ``h`` against control ``n`` — stem gate refuses.
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=50.0))
    seq = DesignSequence.from_controls(
        c, control="n", order=("n", "h"), tolerances=_loose()
    )
    # Override to a tight stem band so the thinner ``h`` cannot unlock.
    seq.tolerances = StyleConsistencyTolerances(
        stem_median=5.0,
        contrast_ratio=10.0,
        entry_rail_y=600.0,
        exit_rail_y=600.0,
        exit_slant_deg=180.0,
        bowl_center_y=300.0,
        ink_ymin=300.0,
        ink_ymax=500.0,
    )
    rep = seq.try_add("h", thin.build("h"))
    assert not rep.passed
    assert seq.unlocked == ("n",)
    assert "h" not in seq.glyphs
    hints = seq.hints_from_last()
    assert hints, "expected actionable fix hints"
    assert any("stem" in h for h in hints)


def test_add_raises_with_hints() -> None:
    c = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=50.0))
    tight = StyleConsistencyTolerances(
        stem_median=5.0,
        contrast_ratio=10.0,
        entry_rail_y=600.0,
        exit_rail_y=600.0,
        exit_slant_deg=180.0,
        bowl_center_y=300.0,
        ink_ymin=300.0,
        ink_ymax=500.0,
    )
    seq = c.design_sequence(order=("n", "h"), control="n", tolerances=tight)
    with pytest.raises(DesignSequenceError) as ei:
        seq.add("h", thin.build("h"))  # type: ignore[union-attr]
    assert ei.value.hints


def test_export_requires_complete() -> None:
    c = Controls.from_context(DesignContext.geometric_sans())
    seq = DesignSequence.from_controls(
        c, control="n", order=("n", "o"), tolerances=_loose()
    )
    with pytest.raises(DesignSequenceError):
        seq.export_glyphs(require_complete=True)
    seq.add("o", c.build("o"))
    assert seq.export_glyphs(require_complete=True)["o"]


def test_default_body_order_starts_with_n_o() -> None:
    order = default_body_design_order()
    assert order[0] == "n"
    assert order[1] == "o"


def test_fix_hints_on_compare() -> None:
    from typekernel.qa.style_consistency import compare_glyph_styles

    c = Controls.from_context(DesignContext.geometric_sans())
    drawn = c.build_all("nh")
    tight = StyleConsistencyTolerances(stem_median=0.01, ink_ymax=0.01)
    rep = compare_glyph_styles(
        drawn["n"], drawn["h"], reference_name="n", candidate_name="h", tolerances=tight
    )
    if not rep.passed:
        hints = rep.fix_hints()
        assert hints
        assert all(isinstance(h, str) and len(h) > 10 for h in hints)


def test_controls_body_design_sequence_completes() -> None:
    """Stock geometric_sans body unlocks under DesignSequence (no build_all)."""
    from typekernel.qa import default_body_design_order

    c = Controls.from_context(DesignContext.geometric_sans())
    order = default_body_design_order()
    seq = c.design_sequence(order=order, control="n")
    for ch in order:
        if ch == seq.control:
            continue
        seq.add(ch, c.build(ch))  # type: ignore[union-attr]
    glyphs = seq.export_glyphs(require_complete=True)  # type: ignore[union-attr]
    assert set(glyphs) == set(order)
    assert seq.is_complete  # type: ignore[union-attr]


def test_controls_body_tolerances_stem_tight() -> None:
    from typekernel.qa.design_sequence import controls_body_tolerances

    tol = controls_body_tolerances()
    assert tol.stem_median == 18.0
    assert tol.stem_median_rel == 0.20
    assert tol.contrast_ratio == 0.45


def test_unlock_controls_body_completes_all_presets() -> None:
    from typekernel.qa.design_sequence import unlock_controls_body

    for factory in (
        DesignContext.geometric_sans,
        DesignContext.humanist_sans,
        DesignContext.code_clear,
    ):
        c = Controls.from_context(factory())
        seq = unlock_controls_body(c)
        assert seq.is_complete
        assert len(seq.unlocked) == len(default_body_design_order())


def test_controls_unlock_body_matches_module_helper() -> None:
    c = Controls.from_context(DesignContext.geometric_sans())
    via_controls = c.unlock_body()
    from typekernel.qa.design_sequence import unlock_controls_body

    via_module = unlock_controls_body(c)
    assert via_controls.unlocked == via_module.unlocked  # type: ignore[union-attr]
    assert via_controls.is_complete  # type: ignore[union-attr]


def test_latin_topology_skips_open_rounds_and_hooks() -> None:
    from typekernel.qa.design_sequence import latin_topology_skip_checks

    nc = latin_topology_skip_checks("n", "c")
    assert "contrast_ratio" in nc
    assert "stem_median" in nc
    nt = latin_topology_skip_checks("n", "t")
    assert "ink_ymin" in nt
    no = latin_topology_skip_checks("n", "o")
    assert "contrast_ratio" in no
    assert "stem_median" not in no


def test_unlock_controls_body_ladder_completes() -> None:
    from typekernel.qa.design_sequence import unlock_controls_body_ladder
    from typekernel.qa.trial_protocol import WEIGHT_LADDER_STEMS

    c = Controls.from_context(DesignContext.geometric_sans())
    seqs = unlock_controls_body_ladder(c)
    assert set(seqs) == set(WEIGHT_LADDER_STEMS)
    assert all(s.is_complete for s in seqs.values())
    via = c.unlock_body_ladder(stems=(70.0, 150.0))
    assert set(via) == {70.0, 150.0}  # type: ignore[arg-type]
    assert all(s.is_complete for s in via.values())  # type: ignore[union-attr]


def test_body_stem_median_ignores_crossbar_on_e() -> None:
    from typekernel.qa.style_consistency import extract_glyph_style_metrics

    c = Controls.from_context(DesignContext.humanist_sans().tuned(stem=150.0)).with_stem_relief()
    n = extract_glyph_style_metrics(c.build("n"))
    e = extract_glyph_style_metrics(c.build("e"))
    assert n.stem_median is not None and e.stem_median is not None
    # Must track the upright stem, not the eye / crossbar full width.
    assert abs(e.stem_median - n.stem_median) < 40.0


def test_diagonal_stem_gated_not_blank_skipped() -> None:
    from typekernel.qa.design_sequence import latin_topology_skip_checks

    # Stable diagonals (v/w) keep stem gating; oriented only for v↔w.
    skips = latin_topology_skip_checks("n", "v")
    assert "stem_median" not in skips
    assert "oriented_stem" in skips
    assert "stem_median" not in latin_topology_skip_checks("v", "w")
    assert "oriented_stem" not in latin_topology_skip_checks("v", "w")
    # Crossing / arm diagonals also gate stem (oriented→vertical-equiv fallback).
    for ch in ("x", "z", "k", "y"):
        assert "stem_median" not in latin_topology_skip_checks("n", ch)


def test_diagonal_stem_pass_and_refuse() -> None:
    from typekernel.qa.design_sequence import controls_body_tolerances, latin_topology_skip_checks
    from typekernel.qa.style_consistency import compare_glyph_styles

    c = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=40.0))
    tol = controls_body_tolerances()
    for ch in ("v", "x", "z", "k", "y"):
        ok = compare_glyph_styles(
            c.build("n"),
            c.build(ch),
            reference_name="n",
            candidate_name=ch,
            tolerances=tol,
            skip_checks=latin_topology_skip_checks("n", ch),
        )
        assert ok.passed, f"same-family {ch} should pass: {ok.fix_hints()}"
        bad = compare_glyph_styles(
            c.build("n"),
            thin.build(ch),
            reference_name="n",
            candidate_name=ch,
            tolerances=tol,
            skip_checks=latin_topology_skip_checks("n", ch),
        )
        assert not bad.passed, f"too-thin {ch} must refuse"
        assert any(f.name == "stem_median" for f in bad.failures), ch


def test_diagonal_stem_ladder_geometric_sans() -> None:
    """Heavy geometric masters: x/z use oriented→vertical-equiv when upright inflates."""
    from typekernel.qa.design_sequence import controls_body_tolerances, latin_topology_skip_checks
    from typekernel.qa.style_consistency import compare_glyph_styles
    from typekernel.qa.trial_protocol import controls_at_ladder_stem

    base = Controls.from_context(DesignContext.geometric_sans())
    tol = controls_body_tolerances()
    for stem in (150.0, 180.0, 200.0):
        sheet = controls_at_ladder_stem(base, stem)
        for ch in ("x", "z", "k", "y", "v", "w"):
            report = compare_glyph_styles(
                sheet.build("n"),
                sheet.build(ch),
                reference_name="n",
                candidate_name=ch,
                tolerances=tol,
                skip_checks=latin_topology_skip_checks("n", ch),
            )
            assert report.passed, f"stem={stem} {ch}: {report.fix_hints()}"


def test_unstable_diag_stem_residual_documented() -> None:
    """Regression: _UNSTABLE_DIAG_STEM must stay empty unless a letter is proven unmeasurable.

    If a letter is re-added, this fails so the skip cannot land silently — pair
    any re-add with a comment in design_sequence.py explaining why probes fail.
    """
    from typekernel.qa import design_sequence as ds

    assert ds._UNSTABLE_DIAG_STEM == frozenset()


def test_oriented_stem_gates_diagonal_pair() -> None:
    from typekernel.qa.design_sequence import controls_body_tolerances, latin_topology_skip_checks
    from typekernel.qa.style_consistency import (
        compare_glyph_styles,
        extract_glyph_style_metrics,
    )

    c = Controls.from_context(DesignContext.geometric_sans())
    assert extract_glyph_style_metrics(c.build("v")).oriented_stem is not None
    report = compare_glyph_styles(
        c.build("v"),
        c.build("w"),
        reference_name="v",
        candidate_name="w",
        tolerances=controls_body_tolerances(),
        skip_checks=latin_topology_skip_checks("v", "w"),
    )
    assert report.passed
    by_name = {ch.name: ch for ch in report.checks}
    assert "oriented_stem" in by_name
    assert by_name["oriented_stem"].ok


def test_unlock_controls_caps_completes() -> None:
    from typekernel.qa.design_sequence import (
        default_cap_design_order,
        unlock_controls_caps,
    )

    c = Controls.from_context(DesignContext.geometric_sans())
    seq = unlock_controls_caps(c)
    assert seq.is_complete
    assert len(seq.unlocked) == len(default_cap_design_order())
    via = c.unlock_caps()
    assert via.unlocked == seq.unlocked  # type: ignore[union-attr]


def test_curved_y_tail_stem_not_hairline() -> None:
    """Descender fracs must not read the curved ``y`` tail as the stem."""
    from typekernel.parts.style import Style
    from typekernel.qa.design_sequence import controls_body_tolerances, latin_topology_skip_checks
    from typekernel.qa.style_consistency import compare_glyph_styles

    ctx = DesignContext.humanist_sans().tuned(
        style=Style(y_tail="curved", a_form="single", g_form="single"),
    )
    c = Controls.from_context(ctx)
    report = compare_glyph_styles(
        c.build("n"),
        c.build("y"),
        reference_name="n",
        candidate_name="y",
        tolerances=controls_body_tolerances(),
        skip_checks=latin_topology_skip_checks("n", "y"),
    )
    assert report.passed, report.fix_hints()



def test_latin_digit_topology_skips_documented() -> None:
    from typekernel.qa.design_sequence import latin_digit_topology_skip_checks

    # Open figures / double bowl: stem probes unreliable.
    for ch in ("2", "3", "5", "8"):
        skips = latin_digit_topology_skip_checks("1", ch)
        assert "stem_median" in skips
        assert "contrast_ratio" in skips
        assert "entry_rail_y" in skips
    # Stem-like figures keep stem gating vs control ``1``.
    for ch in ("0", "4", "7", "6", "9"):
        assert "stem_median" not in latin_digit_topology_skip_checks("1", ch)
    # Diagonals skip contrast only.
    assert "contrast_ratio" in latin_digit_topology_skip_checks("1", "7")
    assert "stem_median" not in latin_digit_topology_skip_checks("1", "7")


def test_unlock_controls_digits_completes() -> None:
    from typekernel.qa.design_sequence import (
        default_digit_design_order,
        unlock_controls_digits,
    )

    for factory in (
        DesignContext.geometric_sans,
        DesignContext.humanist_sans,
        DesignContext.slab_serif,
        DesignContext.code_clear,
    ):
        c = Controls.from_context(factory())
        seq = unlock_controls_digits(c)
        assert seq.is_complete
        assert len(seq.unlocked) == len(default_digit_design_order())
        via = c.unlock_digits()
        assert via.unlocked == seq.unlocked  # type: ignore[union-attr]


def test_unlock_controls_digits_refuses_thin_stem_figure() -> None:
    from typekernel.qa.design_sequence import DesignSequenceError, unlock_controls_digits

    good = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph("4", lambda _H, _O, _c: thin.build("4"))
    with pytest.raises(DesignSequenceError, match="refused glyph '4'"):
        unlock_controls_digits(broken)


def test_unlock_controls_digits_ladder_completes() -> None:
    from typekernel.qa.design_sequence import unlock_controls_digits_ladder

    c = Controls.from_context(DesignContext.geometric_sans())
    out = unlock_controls_digits_ladder(c, stems=(90.0, 150.0, 200.0))
    assert set(out) == {90.0, 150.0, 200.0}
    assert all(seq.is_complete for seq in out.values())
    via = c.unlock_digits_ladder(stems=(90.0, 150.0))
    assert set(via) == {90.0, 150.0}  # type: ignore[arg-type]


def test_capital_j_stem_uses_upper_band_not_hook() -> None:
    """Shallow ``J`` overshoot must not sample the hook hairline as stem."""
    from typekernel.qa.style_consistency import extract_glyph_style_metrics

    # Contrast < 1 + cap_height 700 reproduces the agent-family bold trap.
    ctx = DesignContext.geometric_sans().tuned(stem=140.0, contrast=0.82, cap_height=700.0)
    controls = Controls.from_context(ctx).with_stem_relief()
    h = extract_glyph_style_metrics(controls.build("H")).stem_median
    j = extract_glyph_style_metrics(controls.build("J")).stem_median
    assert h is not None and j is not None
    assert abs(j - h) <= max(30.0, 0.25 * h), (h, j)


def test_cap_diagonal_pairwise_stem_skipped() -> None:
    from typekernel.qa.design_sequence import latin_cap_topology_skip_checks

    skips = latin_cap_topology_skip_checks("V", "W")
    assert "stem_median" in skips
    assert "oriented_stem" in skips


def test_unlock_controls_punct_completes() -> None:
    from typekernel.qa.design_sequence import (
        default_punct_design_order,
        unlock_controls_punct,
    )

    for factory in (
        DesignContext.geometric_sans,
        DesignContext.humanist_sans,
        DesignContext.slab_serif,
        DesignContext.bracketed_serif,
        DesignContext.code_clear,
    ):
        c = Controls.from_context(factory())
        seq = unlock_controls_punct(c)
        assert seq.is_complete
        assert len(seq.unlocked) == len(default_punct_design_order())
        via = c.unlock_punct()
        assert via.unlocked == seq.unlocked  # type: ignore[union-attr]


def test_unlock_controls_punct_refuses_thin_paren() -> None:
    from typekernel.qa.design_sequence import DesignSequenceError, unlock_controls_punct

    good = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph(")", lambda _n, _o, _ctx: thin.build(")"))
    with pytest.raises(DesignSequenceError, match="refused glyph"):
        unlock_controls_punct(broken)


def test_punct_order_covers_punct_forms() -> None:
    from typekernel.parts.punctuation import PUNCT_FORMS
    from typekernel.qa.design_sequence import DEFAULT_PUNCT_DESIGN_ORDER

    assert set(DEFAULT_PUNCT_DESIGN_ORDER) == set(PUNCT_FORMS)


def test_extreme_slab_stem160_caps_hard_fail_documented() -> None:
    """Extreme slab masters still refuse some caps — do not greenwash.

    Stem ≥ 160 on slab_serif can refuse ``M`` / ``Y`` / ``E`` (or later) under honest
    stem probes (``X`` extreme thin landed). Default presets and compose stay
    green; this marks the construction ceiling until those glyphs are redesigned.
    """
    from typekernel.qa.design_sequence import DesignSequenceError, unlock_controls_caps

    c = Controls.from_context(DesignContext.slab_serif().tuned(stem=160.0)).with_stem_relief()
    with pytest.raises(DesignSequenceError, match="refused glyph"):
        unlock_controls_caps(c)


def test_extreme_slab_stem200_body_hard_fail_documented() -> None:
    """Black slab body can refuse ``z`` — measurement/construction ceiling."""
    from typekernel.qa.design_sequence import DesignSequenceError, unlock_controls_body

    c = Controls.from_context(DesignContext.slab_serif().tuned(stem=200.0)).with_stem_relief()
    with pytest.raises(DesignSequenceError, match="refused glyph"):
        unlock_controls_body(c)


def test_unlock_controls_body_refuses_thin_i() -> None:
    """Dotted ``i`` stem stays gated against control ``n`` (skip shrink)."""
    from typekernel.qa.design_sequence import DesignSequenceError, unlock_controls_body

    good = Controls.from_context(DesignContext.geometric_sans())
    thin = Controls.from_context(DesignContext.geometric_sans().tuned(stem=35.0))
    broken = good.with_glyph("i", lambda _n, _o, _ctx: thin.build("i"))
    with pytest.raises(DesignSequenceError, match="refused glyph 'i'"):
        unlock_controls_body(broken)


def test_dotted_letters_keep_stem_gate() -> None:
    from typekernel.qa.design_sequence import latin_topology_skip_checks

    assert "stem_median" not in latin_topology_skip_checks("n", "i")
    assert "stem_median" not in latin_topology_skip_checks("n", "j")
    assert "ink_ymax" in latin_topology_skip_checks("n", "i")
