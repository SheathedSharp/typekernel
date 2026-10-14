"""g and s from the o ring — the lowercase is complete."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import (
    Controls,
    DesignContext,
    build_n,
    build_o,
    g_from_o,
    n_metrics,
    o_metrics,
    s_from_o,
)
from typekernel.parts.control import _hook_shoulder_rise


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


def test_g_hook_in_descender_and_counter(ctx: DesignContext) -> None:
    g = g_from_o(build_o(ctx), build_n(ctx))
    outer, counter = g.solids[0].contours
    assert signed_area(outer) > 0 > signed_area(counter)
    _, y0, _, y1 = bounds(g.solids[0])
    rise = _hook_shoulder_rise(ctx, n_metrics(ctx))
    assert y0 == pytest.approx(ctx.descender - rise)
    assert y1 == pytest.approx(ctx.x_height + ctx.overshoot)
    # below the baseline the hook curls left of the stem
    (stem,) = ink_intervals_at_y(list(g.solids), ctx.descender / 3.0)
    low = ink_intervals_at_y(list(g.solids), ctx.descender + 4.0)
    assert min(r[0] for r in low) < stem[0] - 0.5 * o_metrics(ctx).rx


def test_s_single_contour_crosses_three_times(ctx: DesignContext) -> None:
    s = s_from_o(build_o(ctx))
    (contour,) = s.solids[0].contours
    assert signed_area(contour) > 0
    x0, y0, x1, y1 = bounds(s.solids[0])
    assert y0 == pytest.approx(-ctx.overshoot) and y1 == pytest.approx(ctx.x_height + ctx.overshoot)
    assert x1 - x0 < o_metrics(ctx).width
    # a vertical scan through the middle meets top, spine and bottom strokes
    mid = (x0 + x1) / 2.0
    hits = 0
    prev = False
    for i in range(0, int(ctx.x_height) + 20, 2):
        y = i - 10.0
        inside = any(a <= mid <= b for a, b in ink_intervals_at_y(list(s.solids), y))
        hits += inside and not prev
        prev = inside
    assert hits == 3


def test_g_hook_outer_segment_count_fixed_across_stems() -> None:
    """TK-205: belly fillet detour keeps one segment count for VF."""
    ctx = DesignContext.humanist_sans()
    ref = g_from_o(build_o(ctx), build_n(ctx), ctx)
    ref_n = len(ref.solids[0].contours[0].segments)
    for stem in (30.0, 86.0, 220.0):
        heavy = ctx.tuned(stem=stem)
        g = g_from_o(build_o(heavy), build_n(heavy), heavy)
        assert len(g.solids[0].contours[0].segments) == ref_n


def test_g_interpolates_across_weight_ladder() -> None:
    ctx = DesignContext.humanist_sans()
    charset = "g"
    light = Controls.from_context(ctx.tuned(stem=30.0))
    bold = Controls.from_context(ctx.tuned(stem=220.0))
    reg_font = Font.from_context(ctx, "G Sans", "Regular", weight_class=400)
    reg_font.add_chars(light.build_all(charset))
    bold_font = Font.from_context(ctx, "G Sans", "Bold", weight_class=700)
    bold_font.add_chars(bold.build_all(charset))
    masters = [Master({"wght": 400.0}, reg_font), Master({"wght": 700.0}, bold_font)]
    assert check_masters(masters) == []


def test_s_top_bowl_narrower(ctx: DesignContext) -> None:
    s = s_from_o(build_o(ctx))
    upper = ink_intervals_at_y(list(s.solids), ctx.x_height * 0.78)
    lower = ink_intervals_at_y(list(s.solids), ctx.x_height * 0.22)
    assert max(b for _, b in upper) - min(a for a, _ in upper) < (
        max(b for _, b in lower) - min(a for a, _ in lower)
    )
