"""Part-exit: continuous open apertures a/c/e/s + builders prefer them."""

from __future__ import annotations

from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    a_from_o,
    a_yoke,
    build_n,
    build_o,
    c_from_o,
    c_yoke,
    e_from_o,
    e_yoke,
    s_from_o,
    s_yoke,
)
from typekernel.parts.control import _o_record, _prefer_public_yoke
from typekernel.parts.terminal_openings import apply_terminal_shear
from typekernel.qa.lint import lint_glyph


def _pts(glyph_or_outline) -> tuple[tuple[float, float], ...]:
    solid = (
        glyph_or_outline.solids[0]
        if hasattr(glyph_or_outline, "solids")
        else glyph_or_outline
    )
    return tuple(
        (round(p.x, 3), round(p.y, 3))
        for c in solid.contours
        for s in c.segments
        for p in s.points
    )


def _bad(glyph, ctx, name: str) -> list[str]:
    return [
        i.rule
        for i in lint_glyph(glyph, ctx, glyph_name=name)
        if i.rule in ("R1_winding", "R2_keyhole", "R3_self_intersect")
    ]


def test_opening_yokes_lint_clean() -> None:
    ctx = DesignContext.humanist_sans()
    for name, outline in (
        ("c", c_yoke(ctx)),
        ("e", e_yoke(ctx)),
        ("s", s_yoke(ctx)),
        ("a", a_yoke(ctx)),
    ):
        g = GlyphAssembler(ctx).add(outline).build()
        assert _bad(g, ctx, name) == []
    assert len(c_yoke(ctx).contours) == 1
    assert len(e_yoke(ctx).contours) == 2
    assert len(s_yoke(ctx).contours) == 1
    assert len(a_yoke(ctx).contours) == 2


def test_builders_prefer_opening_yokes_upright_sans() -> None:
    ctx = DesignContext.humanist_sans()
    assert _prefer_public_yoke(ctx) is True
    o, n = build_o(ctx), build_n(ctx)
    assert _pts(c_from_o(o, ctx)) == _pts(GlyphAssembler(ctx).add(c_yoke(ctx)).build())
    assert _pts(e_from_o(o, ctx)) == _pts(GlyphAssembler(ctx).add(e_yoke(ctx)).build())
    assert _pts(s_from_o(o, ctx)) == _pts(GlyphAssembler(ctx).add(s_yoke(ctx)).build())
    # single-storey a applies the same tip shear recipe after the yoke body
    orec = _o_record(o)
    tip = (2.0 * orec.rx - ctx.stem * 0.35, orec.x_height * 0.92)
    sheared = apply_terminal_shear(ctx, a_yoke(ctx, stem_width=ctx.stem), at=tip)
    assert _pts(a_from_o(o, n, ctx)) == _pts(GlyphAssembler(ctx).add(sheared).build())


def test_opening_yoke_opt_out_serif_only() -> None:
    """Serif inlines opt out; italic sans keeps public opening yokes."""
    assert _prefer_public_yoke(DesignContext.slab_serif()) is False
    italic = DesignContext.humanist_sans().tuned(italic_slant_deg=12.0)
    assert _prefer_public_yoke(italic) is True


def test_c_aperture_param_on_yoke() -> None:
    ctx = DesignContext.humanist_sans()
    closed = c_yoke(ctx, aperture=0.1)
    opened = c_yoke(ctx, aperture=0.9)
    assert _pts(closed) != _pts(opened)
