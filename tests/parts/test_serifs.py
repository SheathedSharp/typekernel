"""TK-306: slab serif style and stem anchors."""

from __future__ import annotations

from typekernel.font import Font, Master, check_masters
from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style
from typekernel.qa.lint import lint_controls
from typekernel.qa.outline_hash import composed_glyph_hash


def test_default_serif_none_preserves_n_hash() -> None:
    ctx = DesignContext.geometric_sans()
    base = Controls.from_context(ctx).build("n")
    again = Controls.from_context(ctx, style=Style(serif="none")).build("n")
    assert composed_glyph_hash(base) == composed_glyph_hash(again)


def test_slab_serif_changes_n_outline() -> None:
    plain = Controls.from_context(DesignContext.geometric_sans()).build("n")
    slab = Controls.from_context(DesignContext.slab_serif()).build("n")
    assert composed_glyph_hash(plain) != composed_glyph_hash(slab)


def test_slab_serif_lint_clean_on_full_supported() -> None:
    report = lint_controls(Controls.from_context(DesignContext.slab_serif()))
    assert not report.errors, report.errors


def test_slab_n_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("n"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_serif_changes_n_outline() -> None:
    plain = Controls.from_context(DesignContext.humanist_sans()).build("n")
    bracket = Controls.from_context(DesignContext.bracketed_serif()).build("n")
    assert composed_glyph_hash(plain) != composed_glyph_hash(bracket)


def test_bracketed_inline_bowl_foot_uses_cubic_bracket_corner() -> None:
    from typekernel.parts import b_from_o, build_n, build_o

    ctx = DesignContext.bracketed_serif().tuned(stem=100.0)
    glyph = b_from_o(build_o(ctx), build_n(ctx))
    kinds = [s.kind for s in glyph.solids[0].contours[0].segments]
    # Foot stack on the stem: horiz, cubic fillet, vert, horiz along baseline.
    assert kinds.count("cubic") >= 1
    foot_idx = kinds.index("line")
    while foot_idx + 3 < len(kinds) and kinds[foot_idx : foot_idx + 4] != [
        "line",
        "cubic",
        "line",
        "line",
    ]:
        foot_idx = kinds.index("line", foot_idx + 1)
    assert kinds[foot_idx : foot_idx + 4] == ["line", "cubic", "line", "line"]


def test_bracketed_cap_v_foot_uses_cubic_bracket_fillet() -> None:
    slab = Controls.from_context(DesignContext.slab_serif()).build("V")
    bracket = Controls.from_context(DesignContext.bracketed_serif()).build("V")
    assert composed_glyph_hash(slab) != composed_glyph_hash(bracket)
    kinds = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert kinds.count("cubic") == 2


def test_bracketed_cap_a_uses_cubic_bracket_fillets() -> None:
    slab = Controls.from_context(DesignContext.slab_serif()).build("A")
    bracket = Controls.from_context(DesignContext.bracketed_serif()).build("A")
    assert composed_glyph_hash(slab) != composed_glyph_hash(bracket)
    kinds = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert kinds.count("cubic") == 2


def test_bracketed_cap_a_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(Controls.from_context(ctx.tuned(stem=stems[0])).build("A").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        g = controls.build("A")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("A", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_cap_w_and_x_use_cubic_bracket_fillets() -> None:
    slab = Controls.from_context(DesignContext.slab_serif())
    bracket = Controls.from_context(DesignContext.bracketed_serif())
    for ch in ("W", "X"):
        assert composed_glyph_hash(slab.build(ch)) != composed_glyph_hash(bracket.build(ch))
        kinds = [s.kind for s in bracket.build(ch).solids[0].contours[0].segments]
        assert kinds.count("cubic") == 2


def test_bracketed_cap_wx_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("W", "X"):
        ref_n = len(Controls.from_context(ctx.tuned(stem=stems[0])).build(ch).solids[0].contours[0].segments)
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            controls = Controls.from_context(ctx.tuned(stem=stem))
            g = controls.build(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_v_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(Controls.from_context(ctx.tuned(stem=stems[0])).build("V").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        g = controls.build("V")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("V", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_bowl_glyphs_inline_foot_extends_left_of_plain_stem() -> None:
    """Inline bowl foot serifs must project past the stem (TK-306 bracketed)."""
    from typekernel.optics.space import ink_intervals_at_y
    from typekernel.parts import (
        b_from_o,
        build_n,
        build_o,
        d_from_o,
        p_from_o,
        q_from_o,
    )

    stem = 100.0
    ctx_plain = DesignContext.code_clear().tuned(stem=stem)
    ctx_br = DesignContext.bracketed_serif().tuned(stem=stem)
    builders = {
        "b": b_from_o,
        "d": d_from_o,
        "p": p_from_o,
        "q": q_from_o,
    }

    def left_ink(ctx: DesignContext, letter: str, y_probe: float) -> float:
        o, n = build_o(ctx), build_n(ctx)
        glyph = builders[letter](o, n)
        intervals = ink_intervals_at_y(list(glyph.solids), y_probe)
        assert intervals
        return intervals[0][0]

    for letter in builders:
        y_probe = 0.0 if letter in "bd" else ctx_br.descender + 5.0
        assert left_ink(ctx_br, letter, y_probe) < left_ink(ctx_plain, letter, y_probe) - 8.0


def test_bracketed_serif_lint_clean_on_full_supported() -> None:
    ctx = DesignContext.bracketed_serif()
    report = lint_controls(Controls.from_context(ctx))
    assert not report.errors, report.errors


def test_bracketed_n_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("n"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_serif_masters_on_vf_stable_charset() -> None:
    """Bracketed voice: full supported charset on the four-master weight ladder."""
    ctx = DesignContext.bracketed_serif()
    controls = Controls.from_context(ctx)
    charset = controls.supported
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        tuned = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(tuned.build_all(charset))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_i_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 120.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 500.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("I"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_e_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 120.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 500.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("E"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_nhi_masters_interpolate_on_weight_ladder() -> None:
    """Lowercase + caps share slab stem topology across weights."""
    ctx = DesignContext.slab_serif()
    stems = (70.0, 110.0, 160.0)
    charset = "nHI"
    fonts = []
    for stem, wght in zip(stems, (300.0, 500.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all(charset))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_l_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 120.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 500.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("L"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_serif_masters_on_vf_stable_charset() -> None:
    """Slab voice: full supported charset on the four-master weight ladder."""
    ctx = DesignContext.slab_serif()
    controls = Controls.from_context(ctx)
    charset = controls.supported
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        tuned = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(tuned.build_all(charset))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_opening_caps_change_c_and_g_outline() -> None:
    sans = Controls.from_context(DesignContext.geometric_sans())
    slab = Controls.from_context(DesignContext.slab_serif())
    for ch in ("c", "C", "G"):
        assert composed_glyph_hash(sans.build(ch)) != composed_glyph_hash(slab.build(ch))


def test_slab_cap_cg_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    charset = "CG"
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all(charset))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_t_baked_foot_changes_outline() -> None:
    sans = Controls.from_context(DesignContext.geometric_sans()).build("t")
    slab = Controls.from_context(DesignContext.slab_serif()).build("t")
    assert composed_glyph_hash(sans) != composed_glyph_hash(slab)


def test_slab_t_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("t"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_j_and_q_baked_feet_change_outline() -> None:
    sans = Controls.from_context(DesignContext.geometric_sans())
    slab = Controls.from_context(DesignContext.slab_serif())
    for ch in ("j", "Q"):
        assert composed_glyph_hash(sans.build(ch)) != composed_glyph_hash(slab.build(ch))


def test_slab_cap_q_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("Q"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_j_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("j"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_gqjt_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    charset = "GQjt"
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all(charset))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_r_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("R"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_b_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("B"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_p_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("P"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_d_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("D"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_a_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("A"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_w_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("W"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_v_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("V"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_u_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("U"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_y_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("Y"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_x_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("X"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_z_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("Z"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_k_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("K"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_m_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("M"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_n_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("N"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_cap_t_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 120.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 500.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("T"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_f_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 120.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 500.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("F"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_h_masters_interpolate_on_weight_ladder() -> None:
    """Cap ``H`` bakes slab serifs in one contour for VF-stable segments."""
    ctx = DesignContext.slab_serif()
    stems = (70.0, 120.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 500.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("H"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []
