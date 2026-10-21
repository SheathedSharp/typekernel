"""P R B: the H stem with flattened half bowls; R's leg is spliced in exactly."""

from __future__ import annotations

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import DesignContext, FormSources, h_cap_metrics


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.fixture
def caps(ctx: DesignContext):
    return FormSources.from_context(ctx).derive("PRB")


@pytest.mark.parametrize(("ch", "counters"), [("P", 1), ("R", 1), ("B", 2)])
def test_outer_and_counters(caps, ch: str, counters: int) -> None:
    outer, *rest = caps[ch].solids[0].contours
    assert signed_area(outer) > 0
    assert len(rest) == counters
    assert all(signed_area(k) < 0 for k in rest)


def test_flat_top_and_foot_on_zones(caps, ctx: DesignContext) -> None:
    for ch in "PRB":
        _, y0, _, y1 = bounds(caps[ch].solids[0])
        assert (y0, y1) == pytest.approx((0.0, ctx.cap_height)), ch


def test_p_bowl_upper_half_only(caps, ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    (stem,) = ink_intervals_at_y(list(caps["P"].solids), ctx.cap_height * 0.2)
    assert stem[1] - stem[0] == pytest.approx(h.stem)
    assert len(ink_intervals_at_y(list(caps["P"].solids), ctx.cap_height * 0.75)) == 2


def test_r_leg_reaches_baseline_right(caps, ctx: DesignContext) -> None:
    x1 = bounds(caps["R"].solids[0])[2]
    runs = ink_intervals_at_y(list(caps["R"].solids), 2.0)
    assert len(runs) == 2
    assert runs[-1][1] == pytest.approx(x1, abs=3.0)  # slanted edge, 2 units up


def test_b_upper_bowl_narrower(caps, ctx: DesignContext) -> None:
    upper = ink_intervals_at_y(list(caps["B"].solids), ctx.cap_height * 0.78)
    lower = ink_intervals_at_y(list(caps["B"].solids), ctx.cap_height * 0.25)
    assert max(b for _, b in upper) < max(b for _, b in lower)
