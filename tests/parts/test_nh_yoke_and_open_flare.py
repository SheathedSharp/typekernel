"""Part-exit: shoulder/n/h yoke branching + open-stroke real_flare flags."""

from __future__ import annotations

import pytest

from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    a_from_o,
    build_n,
    build_o,
    c_from_o,
    e_from_o,
    h_yoke,
    n_yoke,
    s_from_o,
    shoulder_yoke,
    v_from_n,
    w_from_n,
)
from typekernel.qa.lint import lint_glyph


def _bad(glyph, ctx, name: str) -> list[str]:
    return [
        i.rule
        for i in lint_glyph(glyph, ctx, glyph_name=name)
        if i.rule in ("R1_winding", "R2_keyhole", "R3_self_intersect")
    ]


def _pts(glyph) -> tuple[tuple[float, float], ...]:
    return tuple(
        (round(p.x, 3), round(p.y, 3))
        for c in glyph.solids[0].contours
        for s in c.segments
        for p in s.points
    )


def test_shoulder_yoke_branch_y_matches_n_yoke() -> None:
    ctx = DesignContext.humanist_sans()
    a = shoulder_yoke(ctx, 40.0, branch_y=True)
    b = n_yoke(ctx, 40.0, branch_y=True)
    assert bounds(a) == bounds(b)
    g = GlyphAssembler(ctx).add(a).build()
    assert _bad(g, ctx, "n_branch") == []
    upright = shoulder_yoke(ctx, 40.0)
    assert bounds(upright) != bounds(a)


def test_h_yoke_uses_ascender_and_branches() -> None:
    ctx = DesignContext.humanist_sans()
    h0 = h_yoke(ctx, 40.0)
    h1 = h_yoke(ctx, 40.0, branch_y=True)
    assert bounds(h0)[3] >= ctx.ascender - 1.0  # stem reaches ascender
    # Branch adds written entry; AABB may match but on-curve points differ.
    assert tuple(
        (round(p.x, 2), round(p.y, 2))
        for c in h0.contours
        for s in c.segments
        for p in s.points
    ) != tuple(
        (round(p.x, 2), round(p.y, 2))
        for c in h1.contours
        for s in c.segments
        for p in s.points
    )
    assert _bad(GlyphAssembler(ctx).add(h1).build(), ctx, "h_branch") == []


def test_open_stroke_real_flare_flags() -> None:
    ctx = DesignContext.humanist_sans()
    o, n = build_o(ctx), build_n(ctx)
    pairs = [
        (c_from_o(o, ctx), c_from_o(o, ctx, real_flare=True)),
        (e_from_o(o, ctx), e_from_o(o, ctx, real_flare=True)),
        (s_from_o(o, ctx), s_from_o(o, ctx, real_flare=True)),
        (a_from_o(o, n, ctx), a_from_o(o, n, ctx, real_flare=True)),
        (v_from_n(n, ctx), v_from_n(n, ctx, real_flare=True)),
        (w_from_n(n, ctx), w_from_n(n, ctx, real_flare=True)),
    ]
    for stock, flared in pairs:
        assert _pts(stock) != _pts(flared)


def test_stock_flared_c_unchanged_without_flag() -> None:
    """terminal_style=flared without real_flare stays on the stock path."""
    ctx = DesignContext.geometric_sans().tuned(terminal_style="flared")
    o = build_o(ctx)
    # c draws vertical cuts; stock flared does not auto-switch to flare_end.
    a = c_from_o(o, ctx, real_flare=False)
    b = c_from_o(o, ctx, real_flare=True)
    assert _pts(a) != _pts(b)


def test_branch_y_rejects_bad_values() -> None:
    ctx = DesignContext.geometric_sans()
    with pytest.raises(ValueError, match="branch_y"):
        n_yoke(ctx, branch_y=ctx.x_height)
    with pytest.raises(ValueError, match="branch_y"):
        h_yoke(ctx, branch_y=-5.0)
