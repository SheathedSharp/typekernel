"""Part-exit: x/z/g real_flare + continuous r_yoke / bowl_stem_yoke."""

from __future__ import annotations

from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    bowl_stem_yoke,
    build_n,
    build_o,
    g_from_o,
    r_yoke,
    x_from_n,
    z_from_n,
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


def test_xzg_real_flare_flags_change_outline() -> None:
    ctx = DesignContext.humanist_sans()
    o, n = build_o(ctx), build_n(ctx)
    pairs = [
        (x_from_n(n, ctx), x_from_n(n, ctx, real_flare=True)),
        (z_from_n(n, ctx), z_from_n(n, ctx, real_flare=True)),
        (g_from_o(o, n, ctx), g_from_o(o, n, ctx, real_flare=True)),
    ]
    for stock, flared in pairs:
        assert _pts(stock) != _pts(flared)
        assert _bad(stock, ctx, "stock") == []
        assert _bad(flared, ctx, "flare") == []


def test_stock_flared_xz_unchanged_without_flag() -> None:
    ctx = DesignContext.geometric_sans().tuned(terminal_style="flared")
    n = build_n(ctx)
    assert _pts(x_from_n(n, ctx)) == _pts(x_from_n(n, ctx, real_flare=False))
    assert _pts(z_from_n(n, ctx)) == _pts(z_from_n(n, ctx, real_flare=False))


def test_r_yoke_single_contour_no_keyhole() -> None:
    ctx = DesignContext.humanist_sans()
    yoke = r_yoke(ctx, 40.0, arm=0.55)
    assert len(yoke.contours) == 1
    g = GlyphAssembler(ctx).add(yoke).build()
    assert _bad(g, ctx, "r_yoke") == []
    # Truncated vs full n shoulder: narrower advance.
    from typekernel.parts import shoulder_yoke

    full = bounds(shoulder_yoke(ctx, 40.0))
    arm = bounds(yoke)
    assert arm[2] < full[2] - ctx.stem * 0.5


def test_r_yoke_branch_y_soft_crotch() -> None:
    ctx = DesignContext.humanist_sans()
    upright = r_yoke(ctx, 40.0)
    branched = r_yoke(ctx, 40.0, branch_y=True)
    assert bounds(upright) != bounds(branched)
    assert _bad(GlyphAssembler(ctx).add(branched).build(), ctx, "r_branch") == []


def test_bowl_stem_yoke_two_contours_no_keyhole() -> None:
    ctx = DesignContext.humanist_sans()
    d_body = bowl_stem_yoke(ctx)
    assert len(d_body.contours) == 2
    assert _bad(GlyphAssembler(ctx).add(d_body).build(), ctx, "d_yoke") == []
    b_body = bowl_stem_yoke(ctx, stem_left=True)
    p_body = bowl_stem_yoke(ctx, stem_left=True, descends=True)
    # Mirror keeps AABB; stem face flips — compare on-curve x of first outer move.
    d0 = d_body.contours[0].segments[0].points[0].x
    b0 = b_body.contours[0].segments[0].points[0].x
    assert abs(d0 - b0) > ctx.stem
    assert bounds(p_body)[1] < -1.0  # reaches descender
    assert _bad(GlyphAssembler(ctx).add(p_body).build(), ctx, "p_yoke") == []
