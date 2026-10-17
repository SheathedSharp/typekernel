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
    assert tol.stem_median == 14.0
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
