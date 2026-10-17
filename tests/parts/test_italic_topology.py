"""TK-403: true italic branching vs construct oblique."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.italic import italic_design, slant_composed_glyph
from typekernel.qa.lint import lint_glyph
from typekernel.qa.originality import topology_signature

_OBLIQUE_VS_ITALIC_CHARS = "aefghkmnruvwy"
_MIN_OUTLINE_DIFFS = 8


def test_italic_n_outline_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = Controls.from_context(DesignContext.humanist_sans())
    sheared = slant_composed_glyph(reg.build_all("n")["n"], 10.0)
    italic = italic_design(reg).build_all("n")["n"]
    assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)


def test_italic_h_outline_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = Controls.from_context(DesignContext.code_clear())
    sheared = slant_composed_glyph(reg.build_all("h")["h"], 10.0)
    italic = italic_design(reg).build_all("h")["h"]
    assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)


def test_italic_branching_n_lint_clean() -> None:
    controls = italic_design(Controls.from_context(DesignContext.geometric_sans()))
    for ch in "nhrum":
        issues = lint_glyph(controls.build_all(ch)[ch], controls.context, glyph_name=ch)
        assert not [i for i in issues if i.severity == "error"]


def test_italic_f_reaches_descender_zone() -> None:
    from typekernel.geo.outline import bounds

    ctx = DesignContext.code_clear()
    reg = Controls.from_context(ctx)
    f_reg = reg.build_all("f")["f"]
    f_ital = italic_design(reg).build_all("f")["f"]
    assert bounds(f_reg.solids[0])[1] == 0.0
    assert bounds(f_ital.solids[0])[1] < ctx.descender * 0.5


def test_italic_a_bowl_narrower_before_slant() -> None:
    from typekernel.geo.outline import bounds
    from typekernel.parts.control import a_from_o, build_n, build_o

    ctx = DesignContext.code_clear().tuned(italic_slant_deg=10.0)
    reg = Controls.from_context(DesignContext.code_clear())
    a_reg = a_from_o(build_o(reg.context), build_n(reg.context), reg.context)
    a_ital = a_from_o(build_o(ctx), build_n(ctx), ctx)
    w_reg = bounds(a_reg.solids[0])[2] - bounds(a_reg.solids[0])[0]
    w_ital = bounds(a_ital.solids[0])[2] - bounds(a_ital.solids[0])[0]
    assert w_ital < w_reg


def test_italic_design_differs_from_construct_oblique_on_key_letters() -> None:
    """TK-403 acceptance: true italic vs sheared regular on branching letters."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = Controls.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    outline_diffs = 0
    topology_diffs = 0
    for ch in _OBLIQUE_VS_ITALIC_CHARS:
        oblique = slant_composed_glyph(reg.build(ch), slant)
        drawn = ital.build(ch)
        if composed_glyph_hash(oblique) != composed_glyph_hash(drawn):
            outline_diffs += 1
        if topology_signature(oblique) != topology_signature(drawn):
            topology_diffs += 1
    assert outline_diffs >= _MIN_OUTLINE_DIFFS
    assert topology_diffs >= 4


def test_italic_ru_topology_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = Controls.from_context(DesignContext.humanist_sans())
    for ch in "ru":
        sheared = slant_composed_glyph(reg.build_all(ch)[ch], 10.0)
        italic = italic_design(reg).build_all(ch)[ch]
        assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)


def test_italic_diagonals_topology_differs_from_shear() -> None:
    """``k/v/w/x/y/z`` cursive-cubic italic ≠ construct shear of upright."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = Controls.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    diffs = 0
    cubic = 0
    for ch in "kvwxyz":
        sheared = slant_composed_glyph(reg.build(ch), slant)
        drawn = ital.build(ch)
        assert composed_glyph_hash(sheared) != composed_glyph_hash(drawn)
        sig = topology_signature(drawn)
        if topology_signature(sheared) != sig:
            diffs += 1
        if any("C" in code for code in sig.contour_codes):
            cubic += 1
    assert diffs == 6
    assert cubic == 6  # cursive cubic crotches (not chamfer-only)


def test_italic_diagonals_match_vf_upright_topology() -> None:
    """VF-compat upright shares italic diagonal topology (segment match)."""
    from typekernel.parts.italic import vf_italic_pair

    up, it = vf_italic_pair(Controls.from_context(DesignContext.geometric_sans()))
    for ch in "kvwxyz":
        assert topology_signature(up.build(ch)) == topology_signature(it.build(ch))


def test_italic_branch_fillet_deeper_than_shear() -> None:
    """Soft branch crotches: ``n``/``h``/``m``/``r``/``u`` gain cubics vs shear."""
    from typekernel.geo.segment import CubicSegment

    reg = Controls.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg

    def n_cubics(g) -> int:
        return sum(
            1
            for solid in g.solids
            for contour in solid.contours
            for seg in contour.segments
            if isinstance(seg, CubicSegment)
        )

    deeper = 0
    for ch in "nhmru":
        drawn = ital.build(ch)
        sheared = slant_composed_glyph(reg.build(ch), slant)
        assert topology_signature(drawn) != topology_signature(sheared)
        if n_cubics(drawn) > n_cubics(sheared):
            deeper += 1
    assert deeper == 5


def test_italic_branch_fillet_vf_pair_matches_on_presets() -> None:
    """Construction-time fillet keeps VF upright/italic topology aligned."""
    from typekernel.parts.italic import vf_italic_pair

    for factory in (
        DesignContext.humanist_sans,
        DesignContext.geometric_sans,
        DesignContext.code_clear,
    ):
        up, it = vf_italic_pair(Controls.from_context(factory()))
        for ch in "nhmru":
            assert topology_signature(up.build(ch)) == topology_signature(it.build(ch))



def test_italic_u_soft_branch_survives_weight_relief() -> None:
    """Soft ``u`` (crotch soften) keeps topology under double stem-relief / ``_font``.

    Regression lock: construction-time ``_emit_italic_branch_shoulder`` on a
    mirrored ``u`` drops a segment when counter grows (see emit docstring).
    """
    from dataclasses import replace

    import tests.parts.test_oblique_compat as oblique_t
    from typekernel.font import Master, check_masters
    from typekernel.parts.italic import vf_italic_pair

    ctx = DesignContext.humanist_sans()
    up, it = vf_italic_pair(Controls.from_context(ctx))
    bold = vf_italic_pair(Controls.from_context(ctx.tuned(stem=120.0)).with_stem_relief())[0]
    sheet = replace(bold, context=bold.context.tuned(stem=120.0)).with_stem_relief()
    codes = {
        topology_signature(up.build("u")).contour_codes,
        topology_signature(it.build("u")).contour_codes,
        topology_signature(bold.build("u")).contour_codes,
        topology_signature(sheet.build("u")).contour_codes,
    }
    assert len(codes) == 1
    masters = [
        Master({"wght": 400, "ital": 0}, oblique_t._font(up, "Regular")),
        Master({"wght": 400, "ital": 1}, oblique_t._font(it, "Italic")),
        Master({"wght": 700, "ital": 0}, oblique_t._font(bold, "Bold", stem=120.0)),
    ]
    assert check_masters(masters) == []


def test_italic_u_emit_on_mirror_breaks_weight_relief() -> None:
    """Living doc: emit fillet on mirrored ``u`` is not weight-stable.

    If this starts passing, emit may have become safe for ``u`` — re-check
    before removing ``_soften_italic_branch_crotch``.
    """
    from dataclasses import replace

    import typekernel.parts.control as ctl
    from typekernel.parts.italic import vf_italic_pair
    from typekernel.parts.transforms import mirror_x

    def emit_mirror_u(m, ctx, *, stem_top):
        return ctl._ccw(
            mirror_x(
                ctl._n_branching_outline(
                    m,
                    stem_top=stem_top,
                    ctx=ctx,
                    shelf_left_foot=ctl._stem_serif_inlined(ctx),
                    soft_branch=True,  # construction emit
                ),
                at_x=m.width / 2.0,
            )
        )

    orig = ctl._u_branching_outline
    ctl._u_branching_outline = emit_mirror_u
    try:
        ctx = DesignContext.humanist_sans()
        bold = vf_italic_pair(Controls.from_context(ctx.tuned(stem=120.0)).with_stem_relief())[0]
        sheet = replace(bold, context=bold.context.tuned(stem=120.0)).with_stem_relief()
        assert topology_signature(bold.build("u")) != topology_signature(sheet.build("u"))
    finally:
        ctl._u_branching_outline = orig
