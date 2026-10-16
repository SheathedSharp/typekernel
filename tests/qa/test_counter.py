"""Counter pinch measurement (R8)."""

from __future__ import annotations

import pytest

from typekernel.parts import Controls, DesignContext
from typekernel.parts.weight_relief import counter_gap_floor
from typekernel.qa.counter import COUNTER_SCAN_MIN_RUN_OVER_STEM, min_counter_gap


def test_counter_scan_min_run_over_stem_frozen() -> None:
    assert COUNTER_SCAN_MIN_RUN_OVER_STEM == 0.09


def test_descender_letters_skip_baseline_stem_pinch() -> None:
    """Stem–bowl slivers below the body band must not drive R8 on ``p``/``q``."""
    ctx = DesignContext.humanist_sans().tuned(stem=180.0)
    controls = Controls.from_context(ctx).with_stem_relief()
    floor = counter_gap_floor(ctx.stem)
    for ch in "pq":
        assert min_counter_gap(controls.build(ch)) >= floor


@pytest.mark.parametrize("ch", ("p", "q"))
def test_descender_micro_sliver_below_min_run_gap_ignored(ch: str) -> None:
    """TK-207: hairline stem–bowl gaps on ``p``/``q`` scanlines stay under ``min_run_gap``."""
    from typekernel.optics.space import ink_intervals_at_y

    ctx = DesignContext.humanist_sans().tuned(stem=180.0)
    controls = Controls.from_context(ctx).with_stem_relief()
    glyph = controls.build(ch)
    min_run = max(1.0, COUNTER_SCAN_MIN_RUN_OVER_STEM * ctx.stem)
    # Grid-audit y where ink splits but gap is far below the R8 scan threshold.
    y_audit = -17.343161198288144
    runs = ink_intervals_at_y(list(glyph.solids), y_audit)
    assert len(runs) >= 2
    pinch = runs[1][0] - runs[0][1]
    assert 0.0 < pinch < min_run
    assert min_counter_gap(glyph) >= counter_gap_floor(ctx.stem)


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


@pytest.mark.parametrize("char", ("f", "h", "i", "j", "l", "r", "t", "z"))
def test_stem_lowercase_pass_counter_floor_across_ladder(char: str) -> None:
    """TK-207: stem / single-stroke lowercase already clear R8 on the weight ladder."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build(char))
            assert gap >= counter_gap_floor(stem)


def test_asterisk_passes_counter_floor_across_ladder() -> None:
    """TK-207: enlarged star arms clear R8 pinch on the weight ladder."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("*"))
            assert gap >= counter_gap_floor(stem)


@pytest.mark.parametrize("char", ("G", "I", "L"))
def test_cap_stem_letters_pass_counter_floor_across_ladder(char: str) -> None:
    """TK-207: straight cap stems already clear R8 on the weight ladder."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build(char))
            assert gap >= counter_gap_floor(stem)


def test_cap_v_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``V`` ladder widen bands clear apex pinch."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("V"))
            assert gap >= counter_gap_floor(stem)


def test_cap_w_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``W`` ladder width bands clear center pinch."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("W"))
            assert gap >= counter_gap_floor(stem)


def test_cap_x_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``X`` mid-ladder slight widen for cross stroke pinch."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("X"))
            assert gap >= counter_gap_floor(stem)


def test_cap_y_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``Y`` mid-ladder junction lift for arm pinch."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("Y"))
            assert gap >= counter_gap_floor(stem)


def test_cap_m_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``M`` widens apex on ladder bands so center crotch clears R8."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("M"))
            assert gap >= counter_gap_floor(stem)


def test_cap_n_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``N`` widens on heavy stems (and high-contrast mid) for R8 headroom."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("N"))
            assert gap >= counter_gap_floor(stem)


def test_k_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``k`` widens by stem band (see cap ``K``) so R8 ladder clears."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("k"))
            assert gap >= counter_gap_floor(stem)


def test_x_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``x`` widens on the ladder so the cross stroke clears R8."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("x"))
            assert gap >= counter_gap_floor(stem)


def test_w_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``w`` widens on the ladder so the middle crotch clears R8."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("w"))
            assert gap >= counter_gap_floor(stem)


def test_v_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``v`` widens on the ladder so the apex crotch clears R8."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("v"))
            assert gap >= counter_gap_floor(stem)


def test_y_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``y`` widens on the ladder so descender crotch clears R8."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("y"))
            assert gap >= counter_gap_floor(stem)


def test_cap_k_passes_counter_floor_across_ladder() -> None:
    """TK-207: ``K`` widens by stem band so R8 ladder stays above floor."""
    from typekernel.parts.weight_relief import STEM_RELIEF_ONSET

    presets = (
        "humanist_sans",
        "geometric_sans",
        "code_clear",
        "paper_ink",
        "open_print",
        "display",
        "mono",
    )
    for preset in presets:
        for stem in (30.0, 70.0, 110.0, 150.0, 180.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = Controls.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.build("K"))
            assert gap >= counter_gap_floor(stem)
