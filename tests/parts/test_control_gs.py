"""g and s from the o ring — the lowercase is complete."""

from __future__ import annotations

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import DesignContext, build_n, build_o, g_from_o, o_metrics, s_from_o


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


def test_g_hook_in_descender_and_counter(ctx: DesignContext) -> None:
    g = g_from_o(build_o(ctx), build_n(ctx))
    outer, counter = g.solids[0].contours
    assert signed_area(outer) > 0 > signed_area(counter)
    _, y0, _, y1 = bounds(g.solids[0])
    assert y0 == pytest.approx(ctx.descender - ctx.overshoot)
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


def test_s_top_bowl_narrower(ctx: DesignContext) -> None:
    s = s_from_o(build_o(ctx))
    upper = ink_intervals_at_y(list(s.solids), ctx.x_height * 0.78)
    lower = ink_intervals_at_y(list(s.solids), ctx.x_height * 0.22)
    assert max(b for _, b in upper) - min(a for a, _ in upper) < (
        max(b for _, b in lower) - min(a for a, _ in lower)
    )
