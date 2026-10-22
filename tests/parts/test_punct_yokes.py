"""Public Usage A punctuation yokes — period, comma, hyphen, quotes."""

from __future__ import annotations

import pytest

from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    build_n,
    build_o,
    comma_from_n_o,
    comma_yoke,
    hyphen_from_n_o,
    hyphen_yoke,
    minus_from_n_o,
    minus_yoke,
    n_metrics,
    period_from_n_o,
    period_yoke,
    quote_ascii_from_n_o,
    quote_ascii_yoke,
    quote_dbl_ascii_from_n_o,
    quote_dbl_ascii_yoke,
    quote_double_left_from_n_o,
    quote_double_left_yoke,
    quote_double_right_from_n_o,
    quote_double_right_yoke,
    quote_single_left_from_n_o,
    quote_single_left_yoke,
    quote_single_right_from_n_o,
    quote_single_right_yoke,
)
from typekernel.parts.punctuation import _dot_size, _with_advance


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.geometric_sans().tuned(
        stem=88.0, x_height=548.0, sidebearing_ratio=0.09
    )


def _glyph_pts(g):
    return tuple(
        p
        for solid in g.solids
        for c in solid.contours
        for s in c.segments
        for p in s.points
    )


def _pack_parts(ctx, m, parts, advance):
    asm = GlyphAssembler(ctx).with_design(m)
    for part in parts:
        asm.add(part)
    return _with_advance(asm.build(), advance)


def test_punct_yokes_match_builders(ctx: DesignContext) -> None:
    n, o = build_n(ctx), build_o(ctx)
    m = n_metrics(ctx)
    size = _dot_size(m, ctx)
    qsize = size * 0.88
    qgap = qsize * 1.05
    hw = m.counter * 0.55
    cases = [
        ("period", period_from_n_o(n, o, ctx), (period_yoke(ctx, n_metrics_rec=m),), size * 1.65),
        ("comma", comma_from_n_o(n, o, ctx), comma_yoke(ctx, n_metrics_rec=m), m.stem * 1.35),
        ("hyphen", hyphen_from_n_o(n, o, ctx), (hyphen_yoke(ctx, n_metrics_rec=m),), hw + m.stem * 0.5),
        ("minus", minus_from_n_o(n, o, ctx), (minus_yoke(ctx, n_metrics_rec=m),), hw + m.stem * 0.5),
        (
            "quote_ascii",
            quote_ascii_from_n_o(n, o, ctx),
            (quote_ascii_yoke(ctx, n_metrics_rec=m),),
            qsize * 1.25,
        ),
        (
            "quote_dbl",
            quote_dbl_ascii_from_n_o(n, o, ctx),
            quote_dbl_ascii_yoke(ctx, n_metrics_rec=m),
            qgap + qsize * 1.1,
        ),
        (
            "quote_single_left",
            quote_single_left_from_n_o(n, o, ctx),
            (quote_single_left_yoke(ctx, n_metrics_rec=m),),
            qsize * 1.25,
        ),
        (
            "quote_single_right",
            quote_single_right_from_n_o(n, o, ctx),
            (quote_single_right_yoke(ctx, n_metrics_rec=m),),
            qsize * 1.25,
        ),
        (
            "quote_double_left",
            quote_double_left_from_n_o(n, o, ctx),
            quote_double_left_yoke(ctx, n_metrics_rec=m),
            qgap + qsize * 1.1,
        ),
        (
            "quote_double_right",
            quote_double_right_from_n_o(n, o, ctx),
            quote_double_right_yoke(ctx, n_metrics_rec=m),
            qgap + qsize * 1.1,
        ),
    ]
    for name, built, parts, advance in cases:
        packed = _pack_parts(ctx, m, parts, advance)
        assert _glyph_pts(built) == _glyph_pts(packed), name
        assert len(built.solids) == len(parts), name
        assert built.advance == pytest.approx(packed.advance), name


def test_period_and_hyphen_are_single_contours(ctx: DesignContext) -> None:
    assert len(period_yoke(ctx).contours) == 1
    assert len(hyphen_yoke(ctx).contours) == 1
    assert len(comma_yoke(ctx)) == 2
