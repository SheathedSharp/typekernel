"""Counter pinch measurement (R8)."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.weight_relief import counter_gap_floor
from typekernel.qa.counter import min_counter_gap


def test_descender_letters_skip_baseline_stem_pinch() -> None:
    """Stem–bowl slivers below the body band must not drive R8 on ``p``/``q``."""
    ctx = DesignContext.humanist_sans().tuned(stem=180.0)
    controls = Controls.from_context(ctx).with_stem_relief()
    floor = counter_gap_floor(ctx.stem)
    for ch in "pq":
        assert min_counter_gap(controls.build(ch)) >= floor


def test_bowl_stem_uses_inner_contour_not_even_odd_sliver() -> None:
    ctx = DesignContext.humanist_sans().tuned(stem=30.0)
    gap = min_counter_gap(Controls.from_context(ctx).build("b"))
    assert gap >= counter_gap_floor(ctx.stem)


def test_round_bowl_still_reports_counter_gap() -> None:
    ctx = DesignContext.humanist_sans().tuned(stem=110.0)
    controls = Controls.from_context(ctx).with_stem_relief()
    gap = min_counter_gap(controls.build("o"))
    floor = counter_gap_floor(ctx.stem)
    assert gap >= floor


def test_cap_k_ignores_stem_diagonal_micro_slivers() -> None:
    """``K`` stem–arm wedges must not dominate R8 (see TK-207 ``K`` charset audit)."""
    ctx = DesignContext.humanist_sans().tuned(stem=70.0)
    gap = min_counter_gap(Controls.from_context(ctx).build("K"))
    assert gap >= counter_gap_floor(ctx.stem)
