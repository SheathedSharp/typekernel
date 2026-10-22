"""Public Usage A double-storey g yoke (opt-in; single remains default)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.geo.contour import signed_area
from typekernel.parts import (
    DesignContext,
    FormSources,
    g_double_yoke,
    g_from_o,
    g_yoke,
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
    return tuple(
        p for c in outline.contours for s in c.segments for p in s.points
    )


def test_default_g_remains_single_storey(ctx: DesignContext) -> None:
    assert ctx.style.g_form == "single"
    single = g_yoke(ctx)
    double = g_double_yoke(ctx)
    # single: outer + bowl counter; double: sealed multi-loop + two counters
    assert len(single.contours) == 2
    assert len(double.contours) == 5
    assert _pts(single) != _pts(double)


def test_g_double_yoke_matches_builder(ctx: DesignContext) -> None:
    ctx_d = replace(ctx, style=Style(g_form="double"))
    o, n = build_o(ctx_d), build_n(ctx_d)
    built = g_from_o(o, n, ctx_d)
    yoke = g_double_yoke(
        ctx_d, o_metrics_rec=o_metrics(ctx_d), n_metrics_rec=n_metrics(ctx_d)
    )
    y_pos = [c for c in yoke.contours if signed_area(c) > 0]
    y_neg = [c for c in yoke.contours if signed_area(c) < 0]
    b_pos = [c for s in built.solids for c in s.contours]
    b_neg = []
    for hole in built.holes:
        for c in hole.contours:
            b_neg.append(c if signed_area(c) < 0 else __import__(
                "typekernel.geo.contour", fromlist=["reverse_contour"]
            ).reverse_contour(c))
    assert _pts(__import__("typekernel.geo.outline", fromlist=["Outline"]).Outline(tuple(y_pos))) == _pts(
        __import__("typekernel.geo.outline", fromlist=["Outline"]).Outline(tuple(b_pos))
    )
    assert len(y_neg) == len(b_neg)
    assert all(signed_area(c) < 0 for c in y_neg)


def test_g_double_yoke_interpolates_across_stems() -> None:
    ctx = DesignContext.code_clear()
    style = Style(g_form="double")
    stems = (70.0, 110.0, 150.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem), style=style)
        if stem >= 150.0:
            controls = controls.with_stem_relief()
        font = Font.from_context(ctx, "GDouble", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("g"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []
