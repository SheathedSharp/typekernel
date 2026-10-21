"""TK-403: true italic branching vs construct oblique."""

from __future__ import annotations

from typekernel.parts import DesignContext, FormSources
from typekernel.parts.italic import italic_design, slant_composed_glyph
from typekernel.qa.lint import lint_glyph
from typekernel.qa.originality import topology_signature

_OBLIQUE_VS_ITALIC_CHARS = "aefghkmnruvwy"
_MIN_OUTLINE_DIFFS = 8


def test_italic_n_outline_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.humanist_sans())
    sheared = slant_composed_glyph(reg.derive("n")["n"], 10.0)
    italic = italic_design(reg).derive("n")["n"]
    assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)


def test_italic_h_outline_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.code_clear())
    sheared = slant_composed_glyph(reg.derive("h")["h"], 10.0)
    italic = italic_design(reg).derive("h")["h"]
    assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)


def test_italic_branching_n_lint_clean() -> None:
    controls = italic_design(FormSources.from_context(DesignContext.geometric_sans()))
    for ch in "nhrum":
        issues = lint_glyph(controls.derive(ch)[ch], controls.context, glyph_name=ch)
        assert not [i for i in issues if i.severity == "error"]


def test_italic_f_reaches_descender_zone() -> None:
    from typekernel.geo.outline import bounds

    ctx = DesignContext.code_clear()
    reg = FormSources.from_context(ctx)
    f_reg = reg.derive("f")["f"]
    f_ital = italic_design(reg).derive("f")["f"]
    assert bounds(f_reg.solids[0])[1] == 0.0
    assert bounds(f_ital.solids[0])[1] < ctx.descender * 0.5


def test_italic_a_bowl_narrower_before_slant() -> None:
    from typekernel.geo.outline import bounds
    from typekernel.parts.control import a_from_o, build_n, build_o

    ctx = DesignContext.code_clear().tuned(italic_slant_deg=10.0)
    reg = FormSources.from_context(DesignContext.code_clear())
    a_reg = a_from_o(build_o(reg.context), build_n(reg.context), reg.context)
    a_ital = a_from_o(build_o(ctx), build_n(ctx), ctx)
    w_reg = bounds(a_reg.solids[0])[2] - bounds(a_reg.solids[0])[0]
    w_ital = bounds(a_ital.solids[0])[2] - bounds(a_ital.solids[0])[0]
    assert w_ital < w_reg


def test_italic_design_differs_from_construct_oblique_on_key_letters() -> None:
    """TK-403 acceptance: true italic vs sheared regular on branching letters."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    outline_diffs = 0
    topology_diffs = 0
    for ch in _OBLIQUE_VS_ITALIC_CHARS:
        oblique = slant_composed_glyph(reg.derive_one(ch), slant)
        drawn = ital.derive_one(ch)
        if composed_glyph_hash(oblique) != composed_glyph_hash(drawn):
            outline_diffs += 1
        if topology_signature(oblique) != topology_signature(drawn):
            topology_diffs += 1
    assert outline_diffs >= _MIN_OUTLINE_DIFFS
    assert topology_diffs >= 4


def test_italic_ru_topology_differs_from_sheared_regular() -> None:
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.humanist_sans())
    for ch in "ru":
        sheared = slant_composed_glyph(reg.derive(ch)[ch], 10.0)
        italic = italic_design(reg).derive(ch)[ch]
        assert composed_glyph_hash(sheared) != composed_glyph_hash(italic)


def test_italic_diagonals_topology_differs_from_shear() -> None:
    """``k/v/w/x/y/z`` cursive-cubic italic ≠ construct shear of upright."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    diffs = 0
    cubic = 0
    for ch in "kvwxyz":
        sheared = slant_composed_glyph(reg.derive_one(ch), slant)
        drawn = ital.derive_one(ch)
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

    up, it = vf_italic_pair(FormSources.from_context(DesignContext.geometric_sans()))
    for ch in "kvwxyz":
        assert topology_signature(up.derive_one(ch)) == topology_signature(it.derive_one(ch))


def test_italic_branch_fillet_deeper_than_shear() -> None:
    """Soft branch crotches: ``n``/``h``/``m``/``r``/``u`` gain cubics vs shear."""
    from typekernel.geo.segment import CubicSegment

    reg = FormSources.from_context(DesignContext.humanist_sans())
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
        drawn = ital.derive_one(ch)
        sheared = slant_composed_glyph(reg.derive_one(ch), slant)
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
        up, it = vf_italic_pair(FormSources.from_context(factory()))
        for ch in "nhmru":
            assert topology_signature(up.derive_one(ch)) == topology_signature(it.derive_one(ch))



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
    up, it = vf_italic_pair(FormSources.from_context(ctx))
    bold = vf_italic_pair(FormSources.from_context(ctx.tuned(stem=120.0)).with_stem_relief())[0]
    sheet = replace(bold, context=bold.context.tuned(stem=120.0)).with_stem_relief()
    codes = {
        topology_signature(up.derive_one("u")).contour_codes,
        topology_signature(it.derive_one("u")).contour_codes,
        topology_signature(bold.derive_one("u")).contour_codes,
        topology_signature(sheet.derive_one("u")).contour_codes,
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
        bold = vf_italic_pair(FormSources.from_context(ctx.tuned(stem=120.0)).with_stem_relief())[0]
        sheet = replace(bold, context=bold.context.tuned(stem=120.0)).with_stem_relief()
        assert topology_signature(bold.derive_one("u")) != topology_signature(sheet.derive_one("u"))
    finally:
        ctl._u_branching_outline = orig


def _body_cubics(g) -> int:
    from typekernel.geo.segment import CubicSegment

    return sum(
        1
        for seg in g.solids[0].contours[0].segments
        if isinstance(seg, CubicSegment)
    )


def test_italic_stem_terminals_more_written_than_shear() -> None:
    """Entry kick + exit outstroke: ``i``/``l``/``n``/``r`` body gains cubics vs shear."""
    reg = FormSources.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    deeper = 0
    for ch in "ilnr":
        drawn = ital.derive_one(ch)
        sheared = slant_composed_glyph(reg.derive_one(ch), slant)
        assert topology_signature(drawn) != topology_signature(sheared)
        assert "C" in topology_signature(drawn).contour_codes[0]
        if _body_cubics(drawn) > _body_cubics(sheared):
            deeper += 1
    assert deeper == 4


def test_italic_stem_terminals_vf_pair_matches() -> None:
    """Written foot terminals keep VF upright/italic topology aligned."""
    from typekernel.parts.italic import vf_italic_pair

    for factory in (
        DesignContext.humanist_sans,
        DesignContext.geometric_sans,
        DesignContext.code_clear,
    ):
        up, it = vf_italic_pair(FormSources.from_context(factory()))
        for ch in "ilnhrum":
            assert topology_signature(up.derive_one(ch)) == topology_signature(it.derive_one(ch))


def test_italic_r_arm_terminal_is_cubic_not_vertical_cut() -> None:
    """Italic ``r`` arm end is a written cubic, not a sheer vertical lineTo."""
    from typekernel.parts.control import _italic_arm_terminal_cubic, _r_pieces, n_metrics
    from typekernel.parts.italic import italic_design

    ctx = italic_design(FormSources.from_context(DesignContext.geometric_sans())).context
    m = n_metrics(ctx)
    branch_y = m.x_height * 0.5
    drop = m.x_height - branch_y
    mm = m.tuned(
        x_height=branch_y,
        crown_y=m.crown_y - drop * 0.14,
        leg_top=m.leg_top - drop * 0.2,
        join_y=min(m.join_y, branch_y - m.stem * 0.32),
        inner_crown=m.inner_crown - drop * 0.16,
    )
    _s, outer_arm, inner_arm, _x_t = _r_pieces(mm, 0.5)
    cubic = _italic_arm_terminal_cubic(outer_arm[3], inner_arm[0], stem=m.stem)
    # Lean to the right of a vertical cut (written exit).
    assert cubic[1][0] > outer_arm[3][0]
    assert cubic[2][0] > inner_arm[0][0]
    g = FormSources.from_context(ctx).derive_one("r")
    assert "C" in topology_signature(g).contour_codes[0]
    assert _body_cubics(g) >= 6


def test_italic_hook_letters_more_written_than_shear() -> None:
    """``f``/``j``/``t``: entry kicks + written hook ends beat construct shear."""
    reg = FormSources.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    deeper = 0
    for ch in "fjt":
        drawn = ital.derive_one(ch)
        sheared = slant_composed_glyph(reg.derive_one(ch), slant)
        assert topology_signature(drawn) != topology_signature(sheared)
        if _body_cubics(drawn) > _body_cubics(sheared):
            deeper += 1
    assert deeper == 3


def test_italic_f_descender_keeps_entry_kick() -> None:
    """Italic ``f`` still reaches the descender and gains a foot cubic."""
    from typekernel.geo.outline import bounds
    from typekernel.geo.segment import CubicSegment

    reg = FormSources.from_context(DesignContext.code_clear())
    ital = italic_design(reg)
    f = ital.derive_one("f")
    assert bounds(f.solids[0])[1] < ital.context.descender * 0.5
    # Lowest band should include a cubic (descender entry kick), not only lines.
    low = [
        seg
        for seg in f.solids[0].contours[0].segments
        if isinstance(seg, CubicSegment)
        and min(p.y for p in seg.points) < ital.context.descender * 0.25
    ]
    assert low


def test_italic_openings_and_a_differ_from_shear() -> None:
    """``a``/``c``/``e``/``s`` italic openings read written vs sheared upright."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    for ch in "aces":
        drawn = ital.derive_one(ch)
        sheared = slant_composed_glyph(reg.derive_one(ch), slant)
        assert composed_glyph_hash(drawn) != composed_glyph_hash(sheared)
        assert topology_signature(drawn) != topology_signature(sheared)


def test_italic_a_crown_exit_adds_cubic() -> None:
    """Single-storey italic ``a`` crown exit is a cubic, not a sharp stem corner."""
    reg = FormSources.from_context(DesignContext.geometric_sans())
    ital = italic_design(reg)
    drawn = ital.derive_one("a")
    sheared = slant_composed_glyph(reg.derive_one("a"), ital.context.italic_slant_deg)
    assert _body_cubics(drawn) > _body_cubics(sheared)


def test_italic_hook_and_opening_vf_pair_matches() -> None:
    """Hook + opening terminal craft keeps VF upright/italic topology aligned."""
    from typekernel.parts.italic import vf_italic_pair

    up, it = vf_italic_pair(FormSources.from_context(DesignContext.humanist_sans()))
    for ch in "fjtaces":
        assert topology_signature(up.derive_one(ch)) == topology_signature(it.derive_one(ch))


def test_italic_caps_stems_more_written_than_shear() -> None:
    """Sans caps ``H``/``I``/``L``/``E``/``F``/``N``/``M``/``T``: entry/exit ≠ shear."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    deeper = 0
    for ch in "HILEFNMT":
        drawn = ital.derive_one(ch)
        sheared = slant_composed_glyph(reg.derive_one(ch), slant)
        assert composed_glyph_hash(drawn) != composed_glyph_hash(sheared)
        assert topology_signature(drawn) != topology_signature(sheared)
        if _body_cubics(drawn) >= _body_cubics(sheared):
            deeper += 1
    # ``I`` may trade rounded-rect corner cubics for foot kicks under slant splits.
    assert deeper >= 6


def test_italic_caps_stems_vf_pair_matches() -> None:
    """Cap stem terminal craft keeps VF upright/italic topology aligned."""
    from typekernel.parts.italic import vf_italic_pair

    up, it = vf_italic_pair(FormSources.from_context(DesignContext.geometric_sans()))
    for ch in "HILEFNMT":
        assert topology_signature(up.derive_one(ch)) == topology_signature(it.derive_one(ch))


def test_italic_cap_diagonals_more_written_than_shear() -> None:
    """Sans caps ``A``/``V``/``W``/``X``/``Y``/``K``/``Z``: crotch/tip craft ≠ shear."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    deeper = 0
    for ch in "AVWXYKZ":
        drawn = ital.derive_one(ch)
        sheared = slant_composed_glyph(reg.derive_one(ch), slant)
        assert composed_glyph_hash(drawn) != composed_glyph_hash(sheared)
        assert topology_signature(drawn) != topology_signature(sheared)
        if _body_cubics(drawn) >= _body_cubics(sheared):
            deeper += 1
    assert deeper >= 5


def test_italic_cap_diagonals_vf_pair_matches() -> None:
    """Cap diagonal crotch craft keeps VF upright/italic topology aligned."""
    from typekernel.parts.italic import vf_italic_pair

    up, it = vf_italic_pair(FormSources.from_context(DesignContext.geometric_sans()))
    for ch in "AVWXYKZ":
        assert topology_signature(up.derive_one(ch)) == topology_signature(it.derive_one(ch))


def test_italic_cap_bowls_more_written_than_shear() -> None:
    """Sans bowl caps ``C``/``G``/``S``/``J``/``U``/``R``: tip craft ≠ shear."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.humanist_sans())
    ital = italic_design(reg)
    slant = ital.context.italic_slant_deg
    deeper = 0
    for ch in "CGSJUR":
        drawn = ital.derive_one(ch)
        sheared = slant_composed_glyph(reg.derive_one(ch), slant)
        assert composed_glyph_hash(drawn) != composed_glyph_hash(sheared)
        assert topology_signature(drawn) != topology_signature(sheared)
        if _body_cubics(drawn) >= _body_cubics(sheared):
            deeper += 1
    assert deeper >= 5


def test_italic_cap_bowls_vf_pair_matches() -> None:
    """Bowl-cap tip craft keeps VF upright/italic topology aligned."""
    from typekernel.parts.italic import vf_italic_pair

    up, it = vf_italic_pair(FormSources.from_context(DesignContext.geometric_sans()))
    for ch in "CGSJUR":
        assert topology_signature(up.derive_one(ch)) == topology_signature(it.derive_one(ch))


def test_italic_cap_g_tip_shear_changes_hash() -> None:
    """Italic ``G`` tip shear is more than construct slant alone."""
    from typekernel.qa.outline_hash import composed_glyph_hash

    reg = FormSources.from_context(DesignContext.code_clear())
    ital = italic_design(reg)
    drawn = ital.derive_one("G")
    sheared = slant_composed_glyph(reg.derive_one("G"), ital.context.italic_slant_deg)
    assert composed_glyph_hash(drawn) != composed_glyph_hash(sheared)
    assert _body_cubics(drawn) >= _body_cubics(sheared)


