"""Sequential / adjacent glyph style consistency gate."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.qa.style_consistency import (
    StyleConsistencyTolerances,
    check_design_sequence,
    compare_glyph_styles,
    extract_glyph_style_metrics,
    script_body_tolerances,
)


def test_extract_metrics_on_control_n() -> None:
    drawn = Controls.from_context(DesignContext.geometric_sans()).build_all("no")
    m = extract_glyph_style_metrics(drawn["n"])
    assert m.stem_median is not None and m.stem_median > 10.0
    assert m.ink_ymax > m.ink_ymin
    assert m.bowl_center_y > m.ink_ymin


def test_same_glyph_compare_passes() -> None:
    drawn = Controls.from_context(DesignContext.geometric_sans()).build_all("n")
    report = compare_glyph_styles(
        drawn["n"], drawn["n"], reference_name="n", candidate_name="n"
    )
    assert report.passed
    assert all(c.ok for c in report.checks)


def test_n_o_stem_within_budget() -> None:
    drawn = Controls.from_context(DesignContext.geometric_sans()).build_all("no")
    report = compare_glyph_styles(
        drawn["n"], drawn["o"], reference_name="n", candidate_name="o"
    )
    by_name = {c.name: c for c in report.checks}
    assert by_name["stem_median"].delta is not None
    assert by_name["stem_median"].delta <= 25.0


def test_design_sequence_unlocks_control_first() -> None:
    charset = "nhu"
    drawn = Controls.from_context(DesignContext.geometric_sans()).build_all(charset)
    tol = StyleConsistencyTolerances(
        stem_median=30.0,
        contrast_ratio=8.0,
        entry_rail_y=500.0,
        exit_rail_y=500.0,
        exit_slant_deg=180.0,
        bowl_center_y=200.0,
        ink_ymin=200.0,
        ink_ymax=400.0,
    )
    seq = check_design_sequence(
        drawn, list(charset), control="n", tolerances=tol, compare_to_previous=True
    )
    assert seq.control == "n"
    assert seq.unlocked[0] == "n"
    assert seq.passed


def test_script_body_tolerances_factory() -> None:
    tol = script_body_tolerances()
    assert tol.ink_ymax < StyleConsistencyTolerances().ink_ymax
    assert tol.entry_rail_y <= 36.0


def test_script_a_e_pass_body_gate() -> None:
    from examples.zayju_script.design import glyph_a, glyph_e

    report = compare_glyph_styles(
        glyph_a(),
        glyph_e(),
        reference_name="a",
        candidate_name="e",
        tolerances=script_body_tolerances(),
    )
    assert report.passed, [(c.name, c.delta, c.limit) for c in report.failures]
