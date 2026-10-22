"""Public Usage A double-storey a yoke (opt-in; single remains default)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.contour import reverse_contour, signed_area
from typekernel.geo.outline import Outline
from typekernel.parts import (
    DesignContext,
    FormSources,
    a_double_yoke,
    a_from_o,
    a_yoke,
    build_n,
    build_o,
    n_metrics,
    o_metrics,
)
from typekernel.parts.style import Style


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.geometric_sans().tuned(
        stem=88.0, x_height=548.0, sidebearing_ratio=0.09
    )


def _pts(outline):
    return tuple(p for c in outline.contours for s in c.segments for p in s.points)


def test_default_a_remains_single_storey(ctx: DesignContext) -> None:
    assert ctx.style.a_form == "single"
    single = a_yoke(ctx)
    double = a_double_yoke(ctx)
    assert len(single.contours) == 2
    assert len(double.contours) == 3
    assert _pts(single) != _pts(double)


def test_a_double_yoke_matches_builder(ctx: DesignContext) -> None:
    ctx_d = replace(ctx, style=Style(a_form="double"))
    o, n = build_o(ctx_d), build_n(ctx_d)
    built = a_from_o(o, n, ctx_d)
    yoke = a_double_yoke(
        ctx_d, o_metrics_rec=o_metrics(ctx_d), n_metrics_rec=n_metrics(ctx_d)
    )
    y_pos = [c for c in yoke.contours if signed_area(c) > 0]
    y_neg = [c for c in yoke.contours if signed_area(c) < 0]
    b_neg = []
    for hole in built.holes:
        for c in hole.contours:
            b_neg.append(c if signed_area(c) < 0 else reverse_contour(c))
    assert _pts(Outline(tuple(y_pos))) == _pts(Outline(tuple(built.solids[0].contours)))
    assert len(y_neg) == len(b_neg)


def test_a_double_yoke_interpolates_across_stems() -> None:
    ctx = DesignContext.code_clear()
    style = Style(a_form="double")
    stems = (70.0, 86.0, 100.0, 120.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 500.0, 600.0, 650.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem), style=style)
        font = Font.from_context(ctx, "ADouble", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("a"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 500.0, 600.0, 650.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []
