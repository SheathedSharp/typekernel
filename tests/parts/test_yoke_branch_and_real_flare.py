"""Part-exit: branched yokes, u_yoke, letter-builder real_flare flag."""

from __future__ import annotations

import pytest

from typekernel.geo.joins import classify_joins
from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    F_from_H,
    GlyphAssembler,
    T_from_H,
    build_H,
    build_n,
    double_shoulder_yoke,
    f_from_n,
    k_from_n,
    r_from_n,
    u_yoke,
    y_from_n,
)
from typekernel.qa.lint import lint_glyph


def _bad(glyph, ctx, name: str) -> list[str]:
    return [
        i.rule
        for i in lint_glyph(glyph, ctx, glyph_name=name)
        if i.rule in ("R2_keyhole", "R3_self_intersect", "R1_winding")
    ]


def test_double_shoulder_yoke_branch_y_auto_clean() -> None:
    ctx = DesignContext.humanist_sans()
    upright = double_shoulder_yoke(ctx, 40.0)
    branched = double_shoulder_yoke(ctx, 40.0, branch_y=True)
    assert branched.contour_count == 1
    assert bounds(upright) != bounds(branched)
    g = GlyphAssembler(ctx).add(branched).build()
    assert _bad(g, ctx, "m_branch") == []
    assert classify_joins(branched).corners <= 4


def test_double_shoulder_yoke_branch_y_float() -> None:
    ctx = DesignContext.geometric_sans()
    by = ctx.x_height * 0.55
    yoke = double_shoulder_yoke(ctx, 0.0, branch_y=by, written_feet=False)
    g = GlyphAssembler(ctx).add(yoke).build()
    assert _bad(g, ctx, "m_by") == []


def test_u_yoke_upright_and_branched_clean() -> None:
    ctx = DesignContext.humanist_sans()
    u0 = u_yoke(ctx, 40.0)
    u1 = u_yoke(ctx, 40.0, branch_y=True)
    assert u0.contour_count == 1 and u1.contour_count == 1
    assert bounds(u0) != bounds(u1)
    assert _bad(GlyphAssembler(ctx).add(u0).build(), ctx, "u0") == []
    assert _bad(GlyphAssembler(ctx).add(u1).build(), ctx, "u1") == []


def test_r_real_flare_changes_outline_stock_flared_stays_shear() -> None:
    ctx = DesignContext.geometric_sans().tuned(terminal_style="flared")
    n = build_n(ctx)
    stock = r_from_n(n, ctx, real_flare=False)
    real = r_from_n(n, ctx, real_flare=True)
    assert bounds(stock.solids[0]) != bounds(real.solids[0])


def _outline_pts(glyph) -> tuple[tuple[float, float], ...]:
    return tuple(
        (round(p.x, 3), round(p.y, 3))
        for c in glyph.solids[0].contours
        for s in c.segments
        for p in s.points
    )


def test_letter_builders_real_flare_flag() -> None:
    ctx = DesignContext.humanist_sans()
    n = build_n(ctx)
    H = build_H(ctx)
    pairs = [
        (r_from_n(n, ctx), r_from_n(n, ctx, real_flare=True)),
        (f_from_n(n, ctx), f_from_n(n, ctx, real_flare=True)),
        (k_from_n(n, ctx), k_from_n(n, ctx, real_flare=True)),
        (y_from_n(n, ctx), y_from_n(n, ctx, real_flare=True)),
        (F_from_H(H, ctx), F_from_H(H, ctx, real_flare=True)),
        (T_from_H(H, ctx), T_from_H(H, ctx, real_flare=True)),
    ]
    for stock, flared in pairs:
        assert _outline_pts(stock) != _outline_pts(flared)


def test_branch_y_rejects_out_of_range() -> None:
    ctx = DesignContext.geometric_sans()
    with pytest.raises(ValueError, match="branch_y"):
        double_shoulder_yoke(ctx, 0.0, branch_y=ctx.x_height)
    with pytest.raises(ValueError, match="branch_y"):
        u_yoke(ctx, 0.0, branch_y=-1.0)
