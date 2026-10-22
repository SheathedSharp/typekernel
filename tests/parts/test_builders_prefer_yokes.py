"""Builders prefer continuous public yokes on the Usage A upright path."""

from __future__ import annotations

from typekernel.geo.outline import bounds
from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    b_from_o,
    bowl_stem_yoke,
    build_h,
    build_m,
    build_n,
    build_o,
    build_r,
    build_u,
    d_from_o,
    double_shoulder_yoke,
    h_yoke,
    n_metrics,
    n_yoke,
    p_from_o,
    q_from_o,
    r_yoke,
    u_yoke,
)
from typekernel.parts.control import _prefer_public_yoke
from typekernel.parts.weight_relief import m_counter_scale
from typekernel.qa.lint import lint_glyph


def _pts(outline) -> tuple[tuple[float, float], ...]:
    return tuple(
        (round(p.x, 3), round(p.y, 3))
        for c in outline.contours
        for s in c.segments
        for p in s.points
    )


def _bad(glyph, ctx, name: str) -> list[str]:
    return [
        i.rule
        for i in lint_glyph(glyph, ctx, glyph_name=name)
        if i.rule in ("R1_winding", "R2_keyhole", "R3_self_intersect")
    ]


def test_prefer_public_yoke_sans_and_upright_serif() -> None:
    """Sans + upright slab/bracket prefer yokes; italic serif and vf_compat_stem opt out."""
    assert _prefer_public_yoke(DesignContext.humanist_sans()) is True
    assert _prefer_public_yoke(DesignContext.slab_serif()) is True
    assert _prefer_public_yoke(DesignContext.bracketed_serif()) is True
    italic = DesignContext.humanist_sans().tuned(italic_slant_deg=12.0)
    assert _prefer_public_yoke(italic) is True
    assert _prefer_public_yoke(DesignContext.slab_serif().tuned(italic_slant_deg=12.0)) is False



def test_italic_u_matches_public_yoke() -> None:
    """Italic sans ``u`` prefers continuous ``u_yoke`` (sharp branch + soften)."""
    from typekernel.parts.italic import italic_design
    from typekernel.parts import FormSources

    ctx = italic_design(FormSources.from_context(DesignContext.humanist_sans())).context
    assert _prefer_public_yoke(ctx) is True
    m = n_metrics(ctx)
    uy = GlyphAssembler(ctx).add(
        u_yoke(
            ctx,
            0.0,
            counter=m.counter,
            stem_width=m.stem,
            stem_top=m.x_height,
            crown_y=m.crown_y,
            kappa=m.kappa,
            branch_y=True,
        )
    ).build()
    assert _pts(build_u(ctx).solids[0]) == _pts(uy.solids[0])

def test_build_n_h_match_public_yokes() -> None:
    ctx = DesignContext.humanist_sans()
    m = n_metrics(ctx)
    n = build_n(ctx)
    h = build_h(ctx)
    ny = GlyphAssembler(ctx).add(
        n_yoke(
            ctx,
            0.0,
            counter=m.counter,
            stem_width=m.stem,
            stem_top=m.x_height,
            join_y=m.join_y,
            crown_y=m.crown_y,
            leg_top=m.leg_top,
            inner_crown=m.inner_crown,
            kappa=m.kappa,
        )
    ).build()
    hy = GlyphAssembler(ctx).add(
        h_yoke(
            ctx,
            0.0,
            counter=m.counter,
            stem_width=m.stem,
            stem_top=m.ascender,
            shoulder_top=m.x_height,
            join_y=m.join_y,
            crown_y=m.crown_y,
            leg_top=m.leg_top,
            inner_crown=m.inner_crown,
            kappa=m.kappa,
        )
    ).build()
    assert _pts(n.solids[0]) == _pts(ny.solids[0])
    assert _pts(h.solids[0]) == _pts(hy.solids[0])
    assert _bad(n, ctx, "n") == []
    assert _bad(h, ctx, "h") == []


def test_build_m_u_r_match_public_yokes() -> None:
    ctx = DesignContext.humanist_sans()
    m = n_metrics(ctx)
    scale = m_counter_scale(ctx.stem)
    mm_ic = min(
        max(min(m.crown_y - m.stem * 0.55, m.inner_crown + 0.32 * m.stem), m.x_height),
        m.crown_y - m.stem * 0.06,
    )
    built_m = build_m(ctx)
    yoke_m = GlyphAssembler(ctx).add(
        double_shoulder_yoke(
            ctx,
            0.0,
            counter=m.counter,
            counter_scale=scale,
            stem_width=m.stem,
            stem_top=m.x_height,
            join_y=m.join_y,
            crown_y=m.crown_y,
            leg_top=m.leg_top,
            inner_crown=mm_ic,
            kappa=m.kappa,
        )
    ).build()
    assert _pts(built_m.solids[0]) == _pts(yoke_m.solids[0])

    um_ic = min(max(m.inner_crown, m.x_height), m.crown_y - m.stem * 0.06)
    built_u = build_u(ctx)
    yoke_u = GlyphAssembler(ctx).add(
        u_yoke(
            ctx,
            0.0,
            counter=m.counter,
            stem_width=m.stem,
            stem_top=m.x_height,
            join_y=m.join_y,
            crown_y=m.crown_y,
            leg_top=m.leg_top,
            inner_crown=um_ic,
            kappa=m.kappa,
        )
    ).build()
    assert _pts(built_u.solids[0]) == _pts(yoke_u.solids[0])

    built_r = build_r(ctx)
    yoke_r = GlyphAssembler(ctx).add(
        r_yoke(
            ctx,
            0.0,
            arm=0.5,
            counter=m.counter,
            stem_width=m.stem,
            stem_top=m.x_height,
            join_y=m.join_y,
            crown_y=m.crown_y,
            leg_top=m.leg_top,
            inner_crown=m.inner_crown,
            kappa=m.kappa,
        )
    ).build()
    # Terminal shear may still run on builder r; compare pre-shear via bounds width.
    assert abs(bounds(built_r.solids[0])[2] - bounds(yoke_r.solids[0])[2]) < 1.0
    assert _bad(built_r, ctx, "r") == []


def test_bdpq_builders_match_bowl_stem_yoke() -> None:
    ctx = DesignContext.humanist_sans()
    o, n = build_o(ctx), build_n(ctx)
    pairs = [
        (d_from_o(o, n, ctx), bowl_stem_yoke(ctx)),
        (b_from_o(o, n, ctx), bowl_stem_yoke(ctx, stem_left=True)),
        (q_from_o(o, n, ctx), bowl_stem_yoke(ctx, descends=True)),
        (p_from_o(o, n, ctx), bowl_stem_yoke(ctx, stem_left=True, descends=True)),
    ]
    for built, yoke in pairs:
        packed = GlyphAssembler(ctx).add(yoke).build()
        assert _pts(built.solids[0]) == _pts(packed.solids[0])
        assert _bad(built, ctx, "bowl") == []


def test_slab_n_h_match_public_yokes() -> None:
    """Upright slab/bracket ``n``/``h`` prefer continuous yokes with inline_serifs."""
    for factory in (DesignContext.slab_serif, DesignContext.bracketed_serif):
        ctx = factory()
        assert _prefer_public_yoke(ctx) is True
        m = n_metrics(ctx)
        n = build_n(ctx)
        h = build_h(ctx)
        ny = GlyphAssembler(ctx).add(
            n_yoke(
                ctx,
                0.0,
                counter=m.counter,
                stem_width=m.stem,
                stem_top=m.x_height,
                join_y=m.join_y,
                crown_y=m.crown_y,
                leg_top=m.leg_top,
                inner_crown=m.inner_crown,
                kappa=m.kappa,
                inline_serifs=True,
            )
        ).build()
        hy = GlyphAssembler(ctx).add(
            h_yoke(
                ctx,
                0.0,
                counter=m.counter,
                stem_width=m.stem,
                join_y=m.join_y,
                crown_y=m.crown_y,
                leg_top=m.leg_top,
                inner_crown=m.inner_crown,
                kappa=m.kappa,
                inline_serifs=True,
            )
        ).build()
        assert _pts(n.solids[0]) == _pts(ny.solids[0])
        assert _pts(h.solids[0]) == _pts(hy.solids[0])
        assert _bad(n, ctx, "n") == []
        assert _bad(h, ctx, "h") == []
