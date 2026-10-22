"""Public Usage A diagonal yokes wrap the fixed-topology builders."""

from __future__ import annotations

from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    k_from_n,
    k_yoke,
    v_from_n,
    v_yoke,
    w_yoke,
    x_yoke,
    y_yoke,
    z_yoke,
    build_n,
)
from typekernel.qa.lint import lint_glyph


def _ctx() -> DesignContext:
    return DesignContext.geometric_sans().tuned(stem=88.0, x_height=548.0)


def _bad(glyph, ctx, name: str) -> list[str]:
    return [
        i.rule
        for i in lint_glyph(glyph, ctx, glyph_name=name)
        if i.rule in ("R1_winding", "R2_keyhole", "R3_self_intersect")
    ]


def test_diagonal_yokes_match_builder_topology() -> None:
    ctx = _ctx()
    n = build_n(ctx)
    pairs = [
        ("v", v_yoke(ctx), v_from_n(n, ctx).solids[0]),
        ("k", k_yoke(ctx), k_from_n(n, ctx).solids[0]),
    ]
    for name, yoke, built in pairs:
        assert len(yoke.contours) == len(built.contours) == 1
        assert len(yoke.contours[0].segments) == len(built.contours[0].segments)
        assert _bad(GlyphAssembler(ctx).add(yoke).build(), ctx, name) == []


def test_diagonal_yokes_lint_clean() -> None:
    ctx = _ctx()
    for name, ol in (
        ("v", v_yoke(ctx)),
        ("w", w_yoke(ctx)),
        ("x", x_yoke(ctx)),
        ("y", y_yoke(ctx)),
        ("z", z_yoke(ctx)),
        ("k", k_yoke(ctx)),
    ):
        assert _bad(GlyphAssembler(ctx).add(ol).build(), ctx, name) == []
