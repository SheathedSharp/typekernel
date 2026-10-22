"""Public Usage A lining-figure yokes — digits 0–9."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    FormSources,
    GlyphAssembler,
    cap_o_metrics,
    eight_yoke,
    five_yoke,
    four_yoke,
    h_cap_metrics,
    nine_yoke,
    one_yoke,
    seven_yoke,
    six_yoke,
    three_yoke,
    two_yoke,
    zero_yoke,
)
from typekernel.parts.caps import build_H, build_O
from typekernel.parts.figures import (
    eight_from_O,
    five_from_O,
    four_from_H,
    nine_from_O,
    one_from_H,
    seven_from_H,
    six_from_O,
    three_from_O,
    two_from_O,
    zero_from_O,
)


DIGITS = "0123456789"


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.geometric_sans().tuned(
        stem=88.0, x_height=548.0, sidebearing_ratio=0.09
    )


def _pts(outline):
    return tuple(
        p
        for c in outline.contours
        for s in c.segments
        for p in s.points
    )


def _pack(ctx: DesignContext, outline, design, anchors: dict):
    asm = GlyphAssembler(ctx).with_design(design).add(outline)
    for name, (x, y) in anchors.items():
        asm.anchor(name, x, y)
    return asm.build().solids[0]


def test_all_figure_yokes_match_builders(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    o = cap_o_metrics(ctx)
    H, O = build_H(ctx, h), build_O(ctx, o)
    from typekernel.parts.figures import _anchors, _fig_metrics

    _, _, _, w = _fig_metrics(h)
    cap = h.cap_height
    # five may widen — take anchors from builder
    cases = [
        ("0", zero_from_O(O, H, ctx), zero_yoke(ctx, metrics=h, o_metrics_rec=o)),
        ("1", one_from_H(H, ctx), one_yoke(ctx, metrics=h)),
        ("2", two_from_O(O, H, ctx), two_yoke(ctx, metrics=h, o_metrics_rec=o)),
        ("3", three_from_O(O, H, ctx), three_yoke(ctx, metrics=h, o_metrics_rec=o)),
        ("4", four_from_H(H, ctx), four_yoke(ctx, metrics=h)),
        ("5", five_from_O(O, H, ctx), five_yoke(ctx, metrics=h, o_metrics_rec=o)),
        ("6", six_from_O(O, H, ctx), six_yoke(ctx, metrics=h, o_metrics_rec=o)),
        ("7", seven_from_H(H, ctx), seven_yoke(ctx, metrics=h)),
        ("8", eight_from_O(O, H, ctx), eight_yoke(ctx, metrics=h, o_metrics_rec=o)),
        ("9", nine_from_O(O, H, ctx), nine_yoke(ctx, metrics=h, o_metrics_rec=o)),
    ]
    for name, built, yoke_ol in cases:
        anchors = {a.name: (a.x, a.y) for a in built.anchors}
        assert _pts(built.solids[0]) == _pts(_pack(ctx, yoke_ol, h, anchors)), name


def test_figure_yokes_reach_cap_zones(ctx: DesignContext) -> None:
    h = h_cap_metrics(ctx)
    # flat tops / bottoms at baseline or cap (polygons)
    for name, fn in (
        ("1", one_yoke),
        ("4", four_yoke),
        ("7", seven_yoke),
    ):
        _, y0, _, y1 = bounds(fn(ctx))
        assert y0 == pytest.approx(0.0, abs=0.5), name
        assert y1 == pytest.approx(h.cap_height, abs=0.5), name
    # round zero overshoots
    _, y0, _, y1 = bounds(zero_yoke(ctx))
    assert y0 == pytest.approx(-ctx.overshoot, abs=0.5)
    assert y1 == pytest.approx(h.cap_height + ctx.overshoot, abs=0.5)


def test_figure_digits_interpolate_across_stems() -> None:
    ctx = DesignContext.humanist_sans()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        tuned = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Figs09", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(tuned.derive(DIGITS))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for font, wght in zip(fonts, (300.0, 400.0, 600.0, 700.0), strict=True)
    ]
    assert check_masters(masters) == []


def test_form_sources_digits(ctx: DesignContext) -> None:
    glyphs = FormSources.from_context(ctx).derive(DIGITS)
    assert "".join(sorted(glyphs)) == DIGITS
