"""Related forms derive from the control glyph's design record, not the context."""

from __future__ import annotations

import pytest

from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    NMetrics,
    OMetrics,
    build_h,
    build_n,
    build_o,
    h_from_n,
    i_from_n,
    l_from_n,
    n_metrics,
    o_metrics,
    u_from_n,
)


def _ink_width(g) -> float:
    b = bounds(g.solids[0])
    return b[2] - b[0]


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


def test_control_glyphs_carry_records(ctx: DesignContext) -> None:
    assert build_n(ctx).design == n_metrics(ctx)
    assert isinstance(build_o(ctx).design, OMetrics)
    assert build_o(ctx).design == o_metrics(ctx)


def test_tuned_n_flows_into_related_forms(ctx: DesignContext) -> None:
    default = build_n(ctx)
    tuned_m = n_metrics(ctx).tuned(counter=200.0, stem=110.0)
    n = build_n(ctx, tuned_m)
    assert _ink_width(n) == pytest.approx(tuned_m.width)
    assert _ink_width(n) != pytest.approx(_ink_width(default))

    for related in (h_from_n(n), u_from_n(n)):
        assert related.design is tuned_m
        assert _ink_width(related) == pytest.approx(tuned_m.width)
    assert _ink_width(i_from_n(n)) == pytest.approx(110.0)
    assert _ink_width(l_from_n(n)) == pytest.approx(110.0)


def test_h_shares_n_shoulder_curves(ctx: DesignContext) -> None:
    m = n_metrics(ctx).tuned(kappa=0.6, inner_crown=n_metrics(ctx).inner_crown - 10)
    n = build_n(ctx, m)
    h = h_from_n(n)
    n_cubics = [s.points for s in n.solids[0].contours[0].segments if s.kind == "cubic"]
    h_cubics = [s.points for s in h.solids[0].contours[0].segments if s.kind == "cubic"]
    assert n_cubics == h_cubics
    assert bounds(h.solids[0])[3] == pytest.approx(m.ascender)


def test_related_forms_fall_back_to_context(ctx: DesignContext) -> None:
    from typekernel.parts import vertical_stem
    from typekernel.parts.compose import GlyphAssembler

    plain = GlyphAssembler(ctx).add(vertical_stem(ctx, 0, 0, ctx.x_height)).build()
    assert h_from_n(plain).design == n_metrics(ctx)
    assert build_h(ctx).advance == pytest.approx(h_from_n(plain).advance)


def test_u_baseline_and_crown(ctx: DesignContext) -> None:
    m = n_metrics(ctx)
    u = u_from_n(build_n(ctx))
    assert isinstance(u.design, NMetrics)
    box = bounds(u.solids[0])
    foot_slack = ctx.stem * 0.09 if ctx.roundness < 0.35 else 0.0
    assert box[1] == pytest.approx(0.0, abs=foot_slack)
    assert box[3] == pytest.approx(m.crown_y)
    assert signed_area(u.solids[0].contours[0]) > 0


def test_u_is_n_mirrored_with_right_stem(ctx: DesignContext) -> None:
    m = n_metrics(ctx).tuned(counter=250.0)
    n = build_n(ctx, m)
    u = u_from_n(n)
    assert u.advance == pytest.approx(n.advance, abs=2.0)
    box = bounds(u.solids[0])
    assert box[3] == pytest.approx(m.crown_y)
    foot_slack = ctx.stem * 0.09 if ctx.roundness < 0.35 else 0.0
    assert box[1] == pytest.approx(0.0, abs=foot_slack)


def test_u_low_roundness_baseline_toe_segment_count() -> None:
    """TK-204: square presets add one cubic + shelf at the left baseline toe."""
    low = DesignContext.code_clear()
    high = DesignContext.humanist_sans()
    u_low = u_from_n(build_n(low), low)
    u_high = u_from_n(build_n(high), high)
    assert len(u_low.solids[0].contours[0].segments) == 12
    assert len(u_high.solids[0].contours[0].segments) == 11
    for stem in (30.0, 86.0, 220.0):
        ctx = low.tuned(stem=stem)
        u = u_from_n(build_n(ctx), ctx)
        assert len(u.solids[0].contours[0].segments) == 12


def test_u_baseline_toe_keeps_sentence_g1_budget() -> None:
    from typekernel.qa.score import word_report

    ctx = DesignContext.code_clear()
    u = u_from_n(build_n(ctx), ctx)
    report = word_report([u], ["u"])
    assert report.g1_join_error_count - report.terminal_count <= 1


@pytest.mark.parametrize(
    ("builder", "names"),
    [
        (
            build_n,
            {"top", "bottom", "stem_L_b", "stem_L_t", "stem_R_b"},
        ),
        (
            build_h,
            {"top", "bottom", "stem_L_b", "stem_L_t", "stem_R_b", "stem_R_t"},
        ),
        (build_o, {"top", "bottom"}),
    ],
)
def test_control_anchors(ctx: DesignContext, builder, names) -> None:
    g = builder(ctx)
    assert {a.name for a in g.anchors} == names
    assert g.anchor("bottom").y == 0.0


def test_n_and_o_top_anchor_centered_on_ink(ctx: DesignContext) -> None:
    for g in (build_n(ctx), build_o(ctx)):
        b = bounds(g.solids[0])
        assert g.anchor("top").x == pytest.approx((b[0] + b[2]) / 2, abs=0.5)
        assert g.anchor("top").y == ctx.x_height
