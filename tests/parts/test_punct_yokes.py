"""Public Usage A punctuation yokes — full punct catalog."""

from __future__ import annotations

import pytest

from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    build_n,
    build_o,
    n_metrics,
    o_metrics,
)
from typekernel.parts import punctuation as P
from typekernel.parts.control import _pack
from typekernel.parts.punctuation import _pack_holes, _with_advance


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


def test_all_punct_builders_have_yokes() -> None:
    builders = [n for n in P.__all__ if n.endswith("_from_n_o")]
    for b in builders:
        stem = b[: -len("_from_n_o")]
        assert f"{stem}_yoke" in P.__all__, b


def test_core_punct_yokes_match_builders(ctx: DesignContext) -> None:
    n, o = build_n(ctx), build_o(ctx)
    m, om = n_metrics(ctx), o_metrics(ctx)
    size = P._dot_size(m, ctx)

    cases = [
        ("period", P.period_from_n_o(n, o, ctx), (P.period_yoke(ctx, n_metrics_rec=m),), size * 1.65, "adv"),
        ("comma", P.comma_from_n_o(n, o, ctx), P.comma_yoke(ctx, n_metrics_rec=m), m.stem * 1.35, "adv"),
        ("colon", P.colon_from_n_o(n, o, ctx), P.colon_yoke(ctx, n_metrics_rec=m), m.stem * 1.15, "adv"),
        ("hyphen", P.hyphen_from_n_o(n, o, ctx), (P.hyphen_yoke(ctx, n_metrics_rec=m),), m.counter * 0.55 + m.stem * 0.5, "adv"),
        ("plus", P.plus_from_n_o(n, o, ctx), (P.plus_yoke(ctx, n_metrics_rec=m),), None, "pack"),
        ("slash", P.slash_from_n_o(n, o, ctx), (P.slash_yoke(ctx, n_metrics_rec=m),), None, "pack"),
        ("exclam", P.exclam_from_n_o(n, o, ctx), P.exclam_yoke(ctx, n_metrics_rec=m), None, "pack"),
        (
            "question",
            P.question_from_n_o(n, o, ctx),
            P.question_yoke(ctx, n_metrics_rec=m, o_metrics_rec=om),
            None,
            "pack",
        ),
        (
            "paren",
            P.paren_left_from_n_o(n, o, ctx),
            (P.paren_left_yoke(ctx, n_metrics_rec=m, o_metrics_rec=om),),
            None,
            "pack",
        ),
        ("bracket", P.bracket_left_from_n_o(n, o, ctx), (P.bracket_left_yoke(ctx, n_metrics_rec=m),), None, "pack"),
        ("hash", P.hash_from_n_o(n, o, ctx), (P.hash_yoke(ctx, n_metrics_rec=m),), None, "pack"),
        (
            "dollar",
            P.dollar_from_n_o(n, o, ctx),
            P.dollar_yoke(ctx, n_metrics_rec=m, o_metrics_rec=om),
            None,
            "holes1",
        ),
        (
            "amp",
            P.ampersand_from_n_o(n, o, ctx),
            P.ampersand_yoke(ctx, n_metrics_rec=m, o_metrics_rec=om),
            None,
            "holes2",
        ),
        (
            "percent",
            P.percent_from_n_o(n, o, ctx),
            P.percent_yoke(ctx, n_metrics_rec=m, o_metrics_rec=om),
            None,
            "holes2",
        ),
        (
            "at",
            P.at_sign_from_n_o(n, o, ctx),
            P.at_sign_yoke(ctx, n_metrics_rec=m, o_metrics_rec=om),
            None,
            "holes2",
        ),
        (
            "degree",
            P.degree_from_n_o(n, o, ctx),
            P.degree_yoke(ctx, n_metrics_rec=m, o_metrics_rec=om),
            None,
            "holes_deg",
        ),
    ]
    for name, built, parts, advance, kind in cases:
        if kind == "adv":
            asm = GlyphAssembler(ctx).with_design(m)
            for part in parts:
                asm.add(part)
            packed = _with_advance(asm.build(), advance)
        elif kind == "pack":
            packed = _pack(ctx, m, {}, *parts)
        elif kind == "holes1":
            packed = _pack_holes(ctx, m, parts)
        elif kind == "holes2":
            solids, holes = parts
            packed = _pack_holes(ctx, m, *solids, holes=holes)
        elif kind == "holes_deg":
            outer, hole = parts
            packed = _pack_holes(ctx, m, outer, holes=(hole,))
        else:
            raise AssertionError(kind)
        assert _glyph_pts(built) == _glyph_pts(packed), name


def test_form_sources_full_punct(ctx: DesignContext) -> None:
    from typekernel.parts import FormSources, PUNCT_FORMS

    glyphs = FormSources.from_context(ctx).derive("".join(PUNCT_FORMS))
    assert set(glyphs) == set(PUNCT_FORMS)
