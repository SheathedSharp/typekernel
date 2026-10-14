"""Round capitals: C G Q S from the O, D U J from the H stem and O curve."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts import Controls, DesignContext, cap_o_metrics, h_cap_metrics


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.fixture
def caps(ctx: DesignContext):
    return Controls.from_context(ctx).build_all("OCGQSDUJ")


def _box(g):
    return bounds(g.solids[0])


@pytest.mark.parametrize(("ch", "contours"), [("C", 1), ("G", 1), ("S", 1), ("U", 1), ("J", 1)])
def test_single_contour_caps(caps, ch: str, contours: int) -> None:
    assert len(caps[ch].solids[0].contours) == contours
    assert signed_area(caps[ch].solids[0].contours[0]) > 0


@pytest.mark.parametrize("ch", ["Q", "D"])
def test_caps_with_counter(caps, ch: str) -> None:
    outer, counter = caps[ch].solids[0].contours
    assert signed_area(outer) > 0 > signed_area(counter)


def test_round_caps_overshoot(caps, ctx: DesignContext) -> None:
    for ch in "OCGS":
        _, y0, _, y1 = _box(caps[ch])
        assert y0 == pytest.approx(-ctx.overshoot, abs=0.5), ch
        assert y1 == pytest.approx(ctx.cap_height + ctx.overshoot, abs=0.5), ch
    # D's top and foot are flat strokes on the zones; U / J dip below the baseline
    _, y0, _, y1 = _box(caps["D"])
    assert (y0, y1) == pytest.approx((0.0, ctx.cap_height))
    assert _box(caps["U"])[1] == pytest.approx(-ctx.overshoot)


def test_g_bar_turns_inward(caps, ctx: DesignContext) -> None:
    o = cap_o_metrics(ctx)
    runs = ink_intervals_at_y(list(caps["G"].solids), ctx.cap_height / 2.0 - 0.05 * ctx.cap_height)
    x0 = _box(caps["G"])[0]
    right = max(runs, key=lambda r: r[1])
    assert right[0] < x0 + 1.15 * o.rx  # the bar reaches past the centre


def test_q_tail_below_baseline_and_counter_untouched(caps, ctx: DesignContext) -> None:
    _, y0, _, _ = _box(caps["Q"])
    assert y0 < -ctx.overshoot - 0.05 * ctx.cap_height
    o_counter = caps["O"].solids[0].contours[1]
    q_counter = caps["Q"].solids[0].contours[1]
    assert abs(signed_area(q_counter)) == pytest.approx(abs(signed_area(o_counter)), rel=1e-6)


def test_j_outer_segment_count_fixed_across_stems() -> None:
    ctx = DesignContext.humanist_sans()
    ref = Controls.from_context(ctx).build("J")
    ref_n = len(ref.solids[0].contours[0].segments)
    for stem in (30.0, 86.0, 220.0):
        heavy = ctx.tuned(stem=stem)
        j = Controls.from_context(heavy).build("J")
        assert len(j.solids[0].contours[0].segments) == ref_n


def test_j_interpolates_across_weight_ladder() -> None:
    ctx = DesignContext.humanist_sans()
    light = Controls.from_context(ctx.tuned(stem=30.0))
    bold = Controls.from_context(ctx.tuned(stem=220.0))
    reg_font = Font.from_context(ctx, "J Sans", "Regular", weight_class=400)
    reg_font.add_chars(light.build_all("J"))
    bold_font = Font.from_context(ctx, "J Sans", "Bold", weight_class=700)
    bold_font.add_chars(bold.build_all("J"))
    masters = [Master({"wght": 400.0}, reg_font), Master({"wght": 700.0}, bold_font)]
    assert check_masters(masters) == []


def test_u_and_j_use_cap_stems(caps, ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    left, right = ink_intervals_at_y(list(caps["U"].solids), ctx.cap_height * 0.8)
    assert left[1] - left[0] == pytest.approx(h.stem)
    assert right[1] - right[0] == pytest.approx(h.stem)
    (stem,) = ink_intervals_at_y(list(caps["J"].solids), ctx.cap_height * 0.8)
    assert stem[1] - stem[0] == pytest.approx(h.stem)
