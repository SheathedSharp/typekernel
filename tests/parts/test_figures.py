"""Lining figures from the cap H / O records, and tabular spacing."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.contour import signed_area
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import FIGURE_FORMS, DesignContext, FormSources, h_cap_metrics, tabular
from typekernel.parts.figures import FIGURE_STEM_RATIO
from typekernel.parts.weight_relief import STEM_RELIEF_ONSET, counter_gap_floor
from typekernel.qa.counter import min_counter_gap

COUNTERS = {"0": 1, "4": 1, "6": 1, "8": 2, "9": 1}


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.fixture
def figures(ctx: DesignContext):
    return FormSources.from_context(ctx).derive("0123456789")


def test_all_ten_registered() -> None:
    assert "".join(sorted(FIGURE_FORMS)) == "0123456789"


@pytest.mark.parametrize("ch", list("0123456789"))
def test_outer_plus_counters(figures, ch: str) -> None:
    outer, *rest = (k for s in figures[ch].solids for k in s.contours)
    assert signed_area(outer) > 0
    assert len(rest) == COUNTERS.get(ch, 0)
    assert all(signed_area(k) < 0 for k in rest)


def test_three_top_reaches_overshoot(figures, ctx: DesignContext) -> None:
    """TK-206: upper bowl keeps a rounded cap, not a flat shelf at cap height."""
    three = figures["3"]
    _, _, _, y1 = bounds(three.solids[0])
    assert y1 > ctx.cap_height + ctx.overshoot * 0.35


def test_three_outer_segment_count_fixed_across_stems() -> None:
    """TK-206: lining ``3`` keeps one outer topology for VF."""
    ctx = DesignContext.humanist_sans()
    ref = FormSources.from_context(ctx).derive_one("3")
    ref_n = len(ref.solids[0].contours[0].segments)
    for stem in (30.0, 86.0, 220.0):
        three = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("3")
        assert len(three.solids[0].contours[0].segments) == ref_n


def test_three_interpolates_across_weight_ladder() -> None:
    ctx = DesignContext.humanist_sans()
    light = FormSources.from_context(ctx.tuned(stem=30.0))
    bold = FormSources.from_context(ctx.tuned(stem=220.0))
    reg_font = Font.from_context(ctx, "Three Sans", "Regular", weight_class=400)
    reg_font.add_chars(light.derive("3"))
    bold_font = Font.from_context(ctx, "Three Sans", "Bold", weight_class=700)
    bold_font.add_chars(bold.derive("3"))
    masters = [Master({"wght": 400.0}, reg_font), Master({"wght": 700.0}, bold_font)]
    assert check_masters(masters) == []


def test_five_stem_relief_opens_bowl_counter_midweights() -> None:
    """TK-206/207: ``5`` bowl ring thins with stem so ladder R8 stays above floor."""
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
        for stem in (30.0, 70.0, 110.0, 150.0, 200.0):
            ctx = getattr(DesignContext, preset)().tuned(stem=stem)
            controls = FormSources.from_context(ctx)
            if stem >= STEM_RELIEF_ONSET:
                controls = controls.with_stem_relief()
            gap = min_counter_gap(controls.derive_one("5"))
            assert gap >= counter_gap_floor(stem)


def test_one_heavy_stem_flag_relief_opens_pinch() -> None:
    """TK-206/207: ``1`` top flag shrinks so R8 headroom remains at black weights."""
    for preset in ("open_print", "paper_ink", "geometric_sans", "mono"):
        ctx = getattr(DesignContext, preset)().tuned(stem=200.0)
        controls = FormSources.from_context(ctx)
        if 200.0 >= STEM_RELIEF_ONSET:
            controls = controls.with_stem_relief()
        gap = min_counter_gap(controls.derive_one("1"))
        assert gap >= counter_gap_floor(200.0)


def test_lining_height(figures, ctx: DesignContext) -> None:
    for ch, g in figures.items():
        _, y0, _, y1 = union_bounds(list(g.solids))
        assert y1 == pytest.approx(ctx.cap_height, abs=ctx.overshoot + 0.5), ch
        assert y0 == pytest.approx(0.0, abs=ctx.overshoot + 0.5), ch


def test_figure_stroke_lighter_than_cap_stem(figures, ctx: DesignContext) -> None:
    t = h_cap_metrics(ctx).stem * FIGURE_STEM_RATIO
    (stem,) = ink_intervals_at_y(list(figures["1"].solids), ctx.cap_height * 0.3)
    assert stem[1] - stem[0] == pytest.approx(t)
    assert t < h_cap_metrics(ctx).stem


def test_tabular_gives_one_advance_with_centred_ink(figures) -> None:
    tab = tabular(figures)
    advances = {g.advance for g in tab.values()}
    assert len(advances) == 1
    adv = advances.pop()
    assert adv == pytest.approx(max(g.advance for g in figures.values()))
    for ch, g in tab.items():
        x0, _, x1, _ = union_bounds(list(g.solids))
        assert x0 == pytest.approx(adv - x1, abs=1e-6), ch
        assert g.anchors == tuple(
            type(a)(a.name, a.x + (x0 - bounds(figures[ch].solids[0])[0]), a.y)
            for a in figures[ch].anchors
        )


def test_tabular_explicit_advance(figures) -> None:
    tab = tabular(figures, advance=700.0)
    assert {g.advance for g in tab.values()} == {700.0}
    assert tabular({}) == {}


def test_all_lining_figures_build_under_stress() -> None:
    """TK-302: every lining digit builds at high ``stress`` (``_cut_x`` / ``_ring_parts``)."""
    ctx = DesignContext.geometric_sans().tuned(contrast=0.55, stem=90.0, stress=42.0)
    controls = FormSources.from_context(ctx)
    for ch in "0123456789":
        controls.derive_one(ch)
