"""Stem relief widens counters at black weight without changing topology."""

from __future__ import annotations

from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import DesignContext, FormSources, build_n, build_o
from typekernel.parts.weight_relief import figure_width_floor, min_bowl_stems, stem_weight_fraction


def _counter_gap_at(g, y: float) -> float:
    intervals = ink_intervals_at_y(list(g.solids), y)
    if len(intervals) < 2:
        return 0.0
    return intervals[1][0] - intervals[0][1]


def test_stem_weight_fraction_ramps() -> None:
    assert stem_weight_fraction(76.0) == 0.0
    assert stem_weight_fraction(220.0) == 1.0
    mid = stem_weight_fraction(150.0)
    assert 0.0 < mid < 1.0


def test_relieve_n_o_widens_metrics_at_black() -> None:
    ctx = DesignContext.code_clear().tuned(stem=220.0)
    plain = FormSources.from_context(ctx)
    relieved = plain.with_stem_relief()
    assert relieved.n.counter > plain.n.counter
    assert relieved.o.rx > plain.o.rx


def test_heavy_n_o_counters_wider_with_relief() -> None:
    ctx = DesignContext.code_clear().tuned(stem=220.0)
    plain = FormSources.from_context(ctx)
    relieved = plain.with_stem_relief()
    y = ctx.x_height * 0.55
    n_gap = _counter_gap_at(build_n(ctx, plain.n), y)
    n_rel = _counter_gap_at(build_n(ctx, relieved.n), y)
    assert n_rel > n_gap
    o_gap = _counter_gap_at(build_o(ctx, plain.o), ctx.x_height * 0.5)
    o_rel = _counter_gap_at(build_o(ctx, relieved.o), ctx.x_height * 0.5)
    assert o_rel > o_gap


def test_min_bowl_and_figure_floor_rise_with_stem() -> None:
    assert min_bowl_stems(76.0) == 2.3
    assert min_bowl_stems(220.0) > 2.3
    assert figure_width_floor(220.0) > figure_width_floor(76.0)


def test_heavy_cap_p_wider_than_regular() -> None:
    reg = FormSources.from_context(DesignContext.code_clear()).derive_one("P")
    black = FormSources.from_context(DesignContext.code_clear().tuned(stem=220.0)).derive_one("P")
    w_reg = bounds(reg.solids[0])[2] - bounds(reg.solids[0])[0]
    w_black = bounds(black.solids[0])[2] - bounds(black.solids[0])[0]
    assert w_black > w_reg


def test_relief_does_not_change_regular_stem() -> None:
    ctx = DesignContext.code_clear().tuned(stem=76.0)
    plain = FormSources.from_context(ctx)
    relieved = plain.with_stem_relief()
    assert relieved.n.counter == plain.n.counter
    g_plain = plain.derive_one("n")
    g_rel = relieved.derive_one("n")
    assert len(g_plain.solids[0].contours[0].segments) == len(
        g_rel.solids[0].contours[0].segments
    )
