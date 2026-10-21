"""TK-306: slab serif style and stem anchors."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.parts import DesignContext, FormSources
from typekernel.parts.style import Style
from typekernel.qa.family_gate import collect_family_gate_failures
from typekernel.qa.identity import check_identity_controls
from typekernel.qa.lint import lint_controls, lint_glyph
from typekernel.qa.originality import (
    L3_VOICE_DISTANCE_THRESHOLD,
    l3_voice_criteria_met,
    nearest_voice_distance,
)
from typekernel.qa.outline_hash import composed_glyph_hash


def test_default_serif_none_preserves_n_hash() -> None:
    ctx = DesignContext.geometric_sans()
    base = FormSources.from_context(ctx).derive_one("n")
    again = FormSources.from_context(ctx, style=Style(serif="none")).derive_one("n")
    assert composed_glyph_hash(base) == composed_glyph_hash(again)


def test_slab_serif_changes_n_outline() -> None:
    plain = FormSources.from_context(DesignContext.geometric_sans()).derive_one("n")
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("n")
    assert composed_glyph_hash(plain) != composed_glyph_hash(slab)


def test_slab_n_left_stem_foot_is_inlined() -> None:
    humanist = FormSources.from_context(DesignContext.humanist_sans()).derive_one("n")
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("n")
    assert composed_glyph_hash(humanist) != composed_glyph_hash(slab)
    assert len(slab.solids[0].contours[0].segments) > len(
        humanist.solids[0].contours[0].segments
    )


def test_slab_nh_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in "nh":
        ref_n = len(
            FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments
        )
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_slab_serif_lint_clean_on_full_supported() -> None:
    report = lint_controls(FormSources.from_context(DesignContext.slab_serif()))
    assert not report.errors, report.errors


def test_slab_n_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("n"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_serif_changes_n_outline() -> None:
    plain = FormSources.from_context(DesignContext.humanist_sans()).derive_one("n")
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("n")
    assert composed_glyph_hash(plain) != composed_glyph_hash(bracket)


def test_bracketed_n_left_stem_foot_uses_cubic_bracket_fillet() -> None:
    plain = FormSources.from_context(DesignContext.humanist_sans()).derive_one("n")
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("n")
    assert composed_glyph_hash(plain) != composed_glyph_hash(bracket)
    pk = [s.kind for s in plain.solids[0].contours[0].segments]
    bk = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert bk.count("cubic") >= pk.count("cubic") + 2


def test_slab_m_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(
        FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("m").solids[0].contours[0].segments
    )
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("m")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("m", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_r_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(
        FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("r").solids[0].contours[0].segments
    )
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("r")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("r", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_r_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(
        FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("r").solids[0].contours[0].segments
    )
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("r")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("r", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_m_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(
        FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("m").solids[0].contours[0].segments
    )
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("m")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("m", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_u_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(
        FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("u").solids[0].contours[0].segments
    )
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("u")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("u", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_u_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(
        FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("u").solids[0].contours[0].segments
    )
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("u")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("u", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_serif_u_has_no_spurious_left_foot_anchor() -> None:
    """``u`` only has a right stem foot; bowl side must not get ``stem_L_b``."""
    for factory in (DesignContext.slab_serif, DesignContext.bracketed_serif):
        g = FormSources.from_context(factory()).derive_one("u")
        names = {a.name for a in g.anchors}
        assert "stem_L_b" not in names
        assert "stem_R_b" not in names
        assert "stem_L_t" not in names
        assert "stem_R_t" not in names


def test_serif_h_ascender_cap_inlined_skips_left_top_anchor() -> None:
    for factory in (DesignContext.slab_serif, DesignContext.bracketed_serif):
        g = FormSources.from_context(factory()).derive_one("h")
        names = {a.name for a in g.anchors}
        assert "stem_L_t" not in names
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("h")
    assert "stem_R_t" not in {a.name for a in slab.anchors}
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("h")
    assert "stem_R_t" not in {a.name for a in bracket.anchors}


def test_slab_h_right_leg_cap_inlined_without_boolean_serif() -> None:
    from typekernel.parts.control import h_from_n
    from typekernel.parts.serifs import apply_glyph_serifs

    ctx = DesignContext.slab_serif()
    n = FormSources.from_context(ctx).control_glyphs()[0]
    h = h_from_n(n, ctx)
    assert not [i for i in lint_glyph(h, ctx, glyph_name="h") if i.severity == "error"]
    assert "stem_R_t" not in {a.name for a in h.anchors}
    assert composed_glyph_hash(h) == composed_glyph_hash(apply_glyph_serifs(h))


def test_bracketed_h_from_n_right_leg_cap_inlined_without_boolean_serif() -> None:
    from typekernel.parts.control import h_from_n
    from typekernel.parts.serifs import apply_glyph_serifs

    ctx = DesignContext.bracketed_serif()
    n = FormSources.from_context(ctx).control_glyphs()[0]
    h = h_from_n(n, ctx)
    assert not [i for i in lint_glyph(h, ctx, glyph_name="h") if i.severity == "error"]
    assert "stem_R_t" not in {a.name for a in h.anchors}
    assert composed_glyph_hash(h) == composed_glyph_hash(apply_glyph_serifs(h))


def test_slab_m_shoulder_cap_inlined_skips_left_top_anchor() -> None:
    from typekernel.parts.serifs import apply_glyph_serifs

    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("m")
    assert "stem_L_t" not in {a.name for a in slab.anchors}
    assert composed_glyph_hash(slab) == composed_glyph_hash(apply_glyph_serifs(slab))
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("m")
    assert "stem_L_t" not in {a.name for a in bracket.anchors}
    assert composed_glyph_hash(bracket) == composed_glyph_hash(apply_glyph_serifs(bracket))


def test_slab_r_shoulder_cap_inlined_skips_left_top_anchor() -> None:
    from typekernel.parts.serifs import apply_glyph_serifs

    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("r")
    assert "stem_L_t" not in {a.name for a in slab.anchors}
    assert composed_glyph_hash(slab) == composed_glyph_hash(apply_glyph_serifs(slab))
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("r")
    assert "stem_L_t" not in {a.name for a in bracket.anchors}
    assert composed_glyph_hash(bracket) == composed_glyph_hash(apply_glyph_serifs(bracket))


def test_slab_h_cannot_split_outer_shoulder_at_x_height_without_r3() -> None:
    """``h`` right-leg top serif cannot reuse ``m``'s shoulder split without R3 (TK-306)."""
    from typekernel.geo.path_builder import PathBuilder
    from typekernel.parts.compose import GlyphAssembler
    from typekernel.parts.control import (
        _ccw,
        _curve,
        _n_begin_left_stem,
        _n_inline_left_stem_cap,
        _n_inline_right_stem_foot,
        _shoulder,
        _split,
        n_metrics,
    )
    from typekernel.qa.lint import lint_glyph

    ctx = DesignContext.slab_serif()
    m = n_metrics(ctx)
    s = _shoulder(m)
    xh = m.x_height
    b = PathBuilder()
    _n_begin_left_stem(b, s.l0, s.l1, m.ascender, ctx, m.stem, shelf_foot=False)
    b.lineTo(s.l1, m.ascender)
    _n_inline_left_stem_cap(b, s.l0, s.l1, m.ascender, ctx, m.stem)
    b.lineTo(s.l1, xh)
    _curve(b, s.outer[0])
    split_outer = _split(s.outer[1], xh, horizontal=True)
    assert split_outer is not None
    _curve(b, split_outer[0])
    _curve(b, split_outer[1])
    b.lineTo(s.r1, 0.0)
    _n_inline_right_stem_foot(b, s.r1, ctx, m.stem)
    b.lineTo(s.r0, 0.0)
    b.lineTo(s.r0, m.join_y)
    _curve(b, s.inner[0])
    _curve(b, s.inner[1])
    b.lineTo(s.l1, 0.0)
    b.closePath()
    g = GlyphAssembler(ctx).with_design(m).add(_ccw(b.build())).build()
    rules = {i.rule for i in lint_glyph(g, ctx, glyph_name="h") if i.severity == "error"}
    assert "R3_self_intersect" in rules


def test_slab_apply_glyph_serifs_is_noop_on_supported() -> None:
    from typekernel.parts.serifs import apply_glyph_serifs

    ctx = DesignContext.slab_serif()
    controls = FormSources.from_context(ctx)
    changed: list[tuple[str, list[str]]] = []
    for ch in controls.supported:
        g = controls.derive_one(ch)
        if composed_glyph_hash(g) != composed_glyph_hash(apply_glyph_serifs(g)):
            stems = [a.name for a in g.anchors if a.name.startswith("stem_")]
            changed.append((ch, stems))
    assert changed == []


def test_bracketed_n_shoulder_cap_paths_self_intersect() -> None:
    """Full-width bracketed cap at ``x_height`` R3; shipped ``n`` uses left-face shoulder cap."""
    from typekernel.geo.path_builder import PathBuilder
    from typekernel.parts.compose import GlyphAssembler
    from typekernel.parts.control import (
        _ccw,
        _curve,
        _n_begin_left_stem,
        _n_inline_left_stem_cap,
        _n_inline_right_stem_foot,
        _n_inline_shoulder_left_cap_slab,
        _shoulder,
        n_metrics,
    )
    from typekernel.qa.lint import lint_glyph

    ctx = DesignContext.bracketed_serif()
    m = n_metrics(ctx)
    s = _shoulder(m)
    xh = m.x_height

    b = PathBuilder()
    _n_begin_left_stem(b, s.l0, s.l1, xh, ctx, m.stem, shelf_foot=True)
    b.lineTo(s.l1, xh)
    _n_inline_left_stem_cap(b, s.l0, s.l1, xh, ctx, m.stem)
    _curve(b, s.outer[0])
    _curve(b, s.outer[1])
    b.lineTo(s.r1, 0.0)
    _n_inline_right_stem_foot(b, s.r1, ctx, m.stem)
    b.lineTo(s.r0, 0.0)
    b.lineTo(s.r0, m.join_y)
    _curve(b, s.inner[0])
    _curve(b, s.inner[1])
    b.lineTo(s.l1, 0.0)
    b.closePath()
    g_full = GlyphAssembler(ctx).with_design(m).add(_ccw(b.build())).build()
    assert "R3_self_intersect" in {
        i.rule for i in lint_glyph(g_full, ctx, glyph_name="n") if i.severity == "error"
    }
    # Slab shoulder cap on bracketed ``n`` is lint-clean but not the shipped voice.
    b = PathBuilder()
    _n_begin_left_stem(b, s.l0, s.l1, xh, ctx, m.stem, shelf_foot=True)
    _n_inline_shoulder_left_cap_slab(b, s.l0, xh, ctx, m.stem)
    b.lineTo(s.l1, xh)
    _curve(b, s.outer[0])
    _curve(b, s.outer[1])
    b.lineTo(s.r1, 0.0)
    _n_inline_right_stem_foot(b, s.r1, ctx, m.stem)
    b.lineTo(s.r0, 0.0)
    b.lineTo(s.r0, m.join_y)
    _curve(b, s.inner[0])
    _curve(b, s.inner[1])
    b.lineTo(s.l1, 0.0)
    b.closePath()
    g_slab = GlyphAssembler(ctx).with_design(m).add(_ccw(b.build())).build()
    assert not [
        i for i in lint_glyph(g_slab, ctx, glyph_name="n") if i.severity == "error"
    ]


def test_bracketed_n_pre_serif_outline_lint_clean() -> None:
    from typekernel.parts.control import build_n, n_metrics

    ctx = DesignContext.bracketed_serif()
    n = build_n(ctx, n_metrics(ctx))
    assert not [i for i in lint_glyph(n, ctx, glyph_name="n") if i.severity == "error"]


def test_bracketed_apply_glyph_serifs_is_noop_on_supported() -> None:
    from typekernel.parts.serifs import apply_glyph_serifs

    ctx = DesignContext.bracketed_serif()
    controls = FormSources.from_context(ctx)
    for ch in controls.supported:
        g = controls.derive_one(ch)
        assert composed_glyph_hash(g) == composed_glyph_hash(apply_glyph_serifs(g))


def test_bracketed_h_pre_serif_outline_lint_clean() -> None:
    from typekernel.parts.control import build_h, n_metrics
    from typekernel.parts.serifs import apply_glyph_serifs

    ctx = DesignContext.bracketed_serif()
    h = build_h(ctx, n_metrics(ctx))
    assert not [i for i in lint_glyph(h, ctx, glyph_name="h") if i.severity == "error"]
    assert "stem_R_t" not in {a.name for a in h.anchors}
    assert composed_glyph_hash(h) == composed_glyph_hash(apply_glyph_serifs(h))


def test_bracketed_h_slab_rect_stem_caps_lint_clean() -> None:
    from typekernel.geo.path_builder import PathBuilder
    from typekernel.parts.compose import GlyphAssembler
    from typekernel.parts.control import (
        _ccw,
        _curve,
        _n_begin_left_stem,
        _n_inline_left_stem_cap,
        _n_inline_right_stem_foot,
        _shoulder,
        _split,
        n_metrics,
    )

    ctx = DesignContext.bracketed_serif()
    m = n_metrics(ctx)
    s = _shoulder(m)
    xh = m.x_height
    b = PathBuilder()
    _n_begin_left_stem(b, s.l0, s.l1, m.ascender, ctx, m.stem, shelf_foot=True)
    b.lineTo(s.l1, m.ascender)
    _n_inline_left_stem_cap(
        b, s.l0, s.l1, m.ascender, ctx, m.stem, slab_rect=True
    )
    b.lineTo(s.l1, xh)
    _curve(b, s.outer[0])
    split_outer = _split(s.outer[1], xh, horizontal=True)
    assert split_outer is not None
    _curve(b, split_outer[0])
    b.lineTo(s.r1, xh)
    _n_inline_left_stem_cap(b, s.r0, s.r1, xh, ctx, m.stem, slab_rect=True)
    b.lineTo(s.r1, split_outer[1][3][1])
    b.lineTo(s.r1, 0.0)
    _n_inline_right_stem_foot(b, s.r1, ctx, m.stem)
    b.lineTo(s.r0, 0.0)
    b.lineTo(s.r0, m.join_y)
    _curve(b, s.inner[0])
    _curve(b, s.inner[1])
    b.lineTo(s.l1, 0.0)
    b.closePath()
    g = GlyphAssembler(ctx).with_design(m).add(_ccw(b.build())).build()
    assert not [i for i in lint_glyph(g, ctx, glyph_name="h") if i.severity == "error"]


def test_bracketed_n_shoulder_cap_inlined_skips_left_top_anchor() -> None:
    from typekernel.parts.serifs import apply_glyph_serifs

    n = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("n")
    assert "stem_L_t" not in {a.name for a in n.anchors}
    assert composed_glyph_hash(n) == composed_glyph_hash(apply_glyph_serifs(n))


def test_slab_n_left_shoulder_cap_inlined_without_boolean_serif() -> None:
    from typekernel.parts.control import build_n, n_metrics
    from typekernel.parts.serifs import apply_glyph_serifs

    ctx = DesignContext.slab_serif()
    n = build_n(ctx, n_metrics(ctx))
    assert not [i for i in lint_glyph(n, ctx, glyph_name="n") if i.severity == "error"]
    assert "stem_L_t" not in {a.name for a in n.anchors}
    assert composed_glyph_hash(n) == composed_glyph_hash(apply_glyph_serifs(n))


def test_serif_n_family_inlined_feet_omit_bottom_stem_anchors() -> None:
    """Inlined foot serifs must not leave boolean ``stem_*_b`` sites on these glyphs."""
    for factory in (DesignContext.slab_serif, DesignContext.bracketed_serif):
        ctx = factory()
        for ch in "nmru":
            names = {a.name for a in FormSources.from_context(ctx).derive_one(ch).anchors}
            assert "stem_L_b" not in names
            assert "stem_M_b" not in names
            assert "stem_R_b" not in names
        r_names = {a.name for a in FormSources.from_context(ctx).derive_one("r").anchors}
        assert "stem_L_b" not in r_names
        assert "stem_R_b" not in r_names


def test_bracketed_nh_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in "nh":
        ref_n = len(
            FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments
        )
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_hook_letters_cap_serif_adds_cubic_fillet() -> None:
    """``f``/``t``/``j`` hook cap feet: bracketed adds one cubic vs slab polyline."""
    slab_ctx = DesignContext.slab_serif()
    br_ctx = DesignContext.bracketed_serif()
    for ch in "ftj":
        slab = FormSources.from_context(slab_ctx).derive_one(ch)
        br = FormSources.from_context(br_ctx).derive_one(ch)
        assert composed_glyph_hash(slab) != composed_glyph_hash(br)
        sk = [s.kind for s in slab.solids[0].contours[0].segments]
        bk = [s.kind for s in br.solids[0].contours[0].segments]
        assert bk.count("cubic") == sk.count("cubic") + 1


def test_bracketed_ftj_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in "ftj":
        ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments)
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


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
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("V")
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("V")
    assert composed_glyph_hash(slab) != composed_glyph_hash(bracket)
    kinds = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert kinds.count("cubic") == 2


def test_bracketed_cap_j_uses_cubic_bracket_fillet() -> None:
    sans = FormSources.from_context(DesignContext.humanist_sans())
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    h_g, s_g, b_g = sans.derive_one("J"), slab.derive_one("J"), bracket.derive_one("J")
    assert composed_glyph_hash(h_g) != composed_glyph_hash(b_g)
    assert composed_glyph_hash(s_g) != composed_glyph_hash(b_g)
    s_k = [s.kind for s in s_g.solids[0].contours[0].segments]
    b_k = [s.kind for s in b_g.solids[0].contours[0].segments]
    # Bracket top pad adds one cubic vs square slab pad (sans has its own soft fillets).
    assert b_k.count("cubic") == s_k.count("cubic") + 1


def test_bracketed_cap_j_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("J").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("J")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("J", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_s_opening_uses_cubic_bracket_fillets() -> None:
    sans = FormSources.from_context(DesignContext.humanist_sans())
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("s", "S"):
        h_g, s_g, b_g = sans.derive_one(ch), slab.derive_one(ch), bracket.derive_one(ch)
        assert composed_glyph_hash(h_g) != composed_glyph_hash(b_g)
        assert composed_glyph_hash(s_g) != composed_glyph_hash(b_g)
        s_k = [s.kind for s in s_g.solids[0].contours[0].segments]
        b_k = [s.kind for s in b_g.solids[0].contours[0].segments]
        # Two opening brackets vs slab shelves (sans uses G1 tip bridges instead).
        assert b_k.count("cubic") == s_k.count("cubic") + 2


def test_bracketed_s_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("s", "S"):
        ref_n = len(
            FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments
        )
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_inline_masters_interpolate_on_weight_ladder() -> None:
    """Bracketed caps with cubic/slab inline serifs (excludes round ``O``)."""
    charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    wghts = (300.0, 400.0, 600.0, 700.0)
    ref = {
        ch: len(
            FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments
        )
        for ch in charset
    }
    fonts = []
    for stem, wght in zip(stems, wghts, strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        for ch in charset:
            g = controls.derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref[ch]
            font.add_char(ch, g)
        fonts.append(font)
    masters = [Master({"wght": wght}, font) for wght, font in zip(wghts, fonts, strict=True)]
    assert check_masters(masters) == []


def test_opening_glyph_masters_interpolate_on_weight_ladder() -> None:
    """TK-306: inline opening serifs keep VF topology on c/e/s and derived glyphs."""
    charset = "cCeEsSGQ()?"
    stems = (70.0, 100.0, 140.0, 180.0)
    wghts = (300.0, 400.0, 600.0, 700.0)
    for factory in (DesignContext.slab_serif, DesignContext.bracketed_serif):
        ctx = factory()
        ref = {
            ch: len(
                FormSources.from_context(ctx.tuned(stem=stems[0]))
                .derive_one(ch)
                .solids[0]
                .contours[0]
                .segments
            )
            for ch in charset
        }
        fonts = []
        for stem, wght in zip(stems, wghts, strict=True):
            controls = FormSources.from_context(ctx.tuned(stem=stem))
            font = Font.from_context(ctx, "Serif", f"W{int(wght)}", weight_class=int(wght))
            for ch in charset:
                g = controls.derive_one(ch)
                assert len(g.solids[0].contours[0].segments) == ref[ch]
                font.add_char(ch, g)
            fonts.append(font)
        masters = [Master({"wght": wght}, font) for wght, font in zip(wghts, fonts, strict=True)]
        assert check_masters(masters) == []


def test_bracketed_e_opening_uses_cubic_bracket_fillet() -> None:
    sans = FormSources.from_context(DesignContext.humanist_sans())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    h_g, b_g = sans.derive_one("e"), bracket.derive_one("e")
    assert composed_glyph_hash(h_g) != composed_glyph_hash(b_g)
    h_k = [s.kind for s in h_g.solids[0].contours[0].segments]
    b_k = [s.kind for s in b_g.solids[0].contours[0].segments]
    assert b_k.count("cubic") == h_k.count("cubic") + 1


def test_bracketed_e_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("e").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("e")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("e", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_c_opening_uses_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("c", "C"):
        s_g, b_g = slab.derive_one(ch), bracket.derive_one(ch)
        assert composed_glyph_hash(s_g) != composed_glyph_hash(b_g)
        s_k = [s.kind for s in s_g.solids[0].contours[0].segments]
        b_k = [s.kind for s in b_g.solids[0].contours[0].segments]
        assert b_k.count("cubic") == s_k.count("cubic") + 2


def test_bracketed_c_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("c", "C"):
        ref_n = len(
            FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments
        )
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_g_and_q_use_cubic_bracket_fillet() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("G", "Q"):
        s_g, b_g = slab.derive_one(ch), bracket.derive_one(ch)
        assert composed_glyph_hash(s_g) != composed_glyph_hash(b_g)
        s_k = [s.kind for s in s_g.solids[0].contours[0].segments]
        b_k = [s.kind for s in b_g.solids[0].contours[0].segments]
        assert b_k.count("cubic") == s_k.count("cubic") + 1


def test_bracketed_cap_gq_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("G", "Q"):
        ref_n = len(
            FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments
        )
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_u_uses_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    s_g, b_g = slab.derive_one("U"), bracket.derive_one("U")
    assert composed_glyph_hash(s_g) != composed_glyph_hash(b_g)
    s_k = [s.kind for s in s_g.solids[0].contours[0].segments]
    b_k = [s.kind for s in b_g.solids[0].contours[0].segments]
    assert len(b_k) == len(s_k) + 3
    assert b_k.count("cubic") == s_k.count("cubic") + 2


def test_bracketed_cap_u_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("U").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("U")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("U", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_bowl_caps_dprb_use_cubic_bracket_fillet() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("D", "P", "R", "B"):
        s_g, b_g = slab.derive_one(ch), bracket.derive_one(ch)
        assert composed_glyph_hash(s_g) != composed_glyph_hash(b_g)
        s_k = [s.kind for s in s_g.solids[0].contours[0].segments]
        b_k = [s.kind for s in b_g.solids[0].contours[0].segments]
        assert len(b_k) == len(s_k) + 1
        assert b_k.count("cubic") == s_k.count("cubic") + 1


def test_bracketed_bowl_caps_dprb_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("D", "P", "R", "B"):
        ref_n = len(
            FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments
        )
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_n_uses_four_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("N")
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("N")
    assert composed_glyph_hash(slab) != composed_glyph_hash(bracket)
    kinds = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert kinds.count("cubic") == 4


def test_bracketed_cap_n_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("N").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("N")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("N", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_cap_m_uses_four_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("M")
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("M")
    assert composed_glyph_hash(slab) != composed_glyph_hash(bracket)
    kinds = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert kinds.count("cubic") == 4


def test_bracketed_cap_m_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("M").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("M")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("M", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_cap_e_f_t_use_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("E", "F", "T"):
        assert composed_glyph_hash(slab.derive_one(ch)) != composed_glyph_hash(bracket.derive_one(ch))
        kinds = [s.kind for s in bracket.derive_one(ch).solids[0].contours[0].segments]
        assert kinds.count("cubic") == 2


def test_bracketed_cap_eft_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("E", "F", "T"):
        ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments)
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_i_and_l_use_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("I", "L"):
        assert composed_glyph_hash(slab.derive_one(ch)) != composed_glyph_hash(bracket.derive_one(ch))
        kinds = [s.kind for s in bracket.derive_one(ch).solids[0].contours[0].segments]
        assert kinds.count("cubic") == 2


def test_bracketed_lower_i_and_l_use_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("i", "l"):
        assert composed_glyph_hash(slab.derive_one(ch)) != composed_glyph_hash(bracket.derive_one(ch))
        kinds = [s.kind for s in bracket.derive_one(ch).solids[0].contours[0].segments]
        assert kinds.count("cubic") == 2


def test_bracketed_lower_il_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("i", "l"):
        ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments)
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_il_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("I", "L"):
        ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments)
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_h_uses_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("H")
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("H")
    assert composed_glyph_hash(slab) != composed_glyph_hash(bracket)
    kinds = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert kinds.count("cubic") == 4


def test_bracketed_cap_h_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("H").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("H")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("H", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_cap_a_uses_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("A")
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("A")
    assert composed_glyph_hash(slab) != composed_glyph_hash(bracket)
    kinds = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert kinds.count("cubic") == 2


def test_bracketed_cap_a_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("A").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        g = controls.derive_one("A")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("A", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_cap_y_uses_cubic_bracket_fillets() -> None:
    plain = FormSources.from_context(DesignContext.humanist_sans()).derive_one("Y")
    bracket = FormSources.from_context(DesignContext.bracketed_serif()).derive_one("Y")
    assert composed_glyph_hash(plain) != composed_glyph_hash(bracket)
    kinds = [s.kind for s in bracket.solids[0].contours[0].segments]
    assert kinds.count("cubic") == 3


def test_bracketed_cap_y_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("Y").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        g = controls.derive_one("Y")
        assert len(g.solids[0].contours[0].segments) == ref_n
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_char("Y", g)
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_cap_z_and_k_use_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("Z", "K"):
        assert composed_glyph_hash(slab.derive_one(ch)) != composed_glyph_hash(bracket.derive_one(ch))
        kinds = [s.kind for s in bracket.derive_one(ch).solids[0].contours[0].segments]
        assert kinds.count("cubic") == 2


def test_bracketed_cap_zk_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("Z", "K"):
        ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments)
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_bracketed_cap_w_and_x_use_cubic_bracket_fillets() -> None:
    slab = FormSources.from_context(DesignContext.slab_serif())
    bracket = FormSources.from_context(DesignContext.bracketed_serif())
    for ch in ("W", "X"):
        assert composed_glyph_hash(slab.derive_one(ch)) != composed_glyph_hash(bracket.derive_one(ch))
        kinds = [s.kind for s in bracket.derive_one(ch).solids[0].contours[0].segments]
        assert kinds.count("cubic") == 2


def test_bracketed_cap_wx_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("W", "X"):
        ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments)
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            controls = FormSources.from_context(ctx.tuned(stem=stem))
            g = controls.derive_one(ch)
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
    ref_n = len(FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one("V").solids[0].contours[0].segments)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        g = controls.derive_one("V")
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
    report = lint_controls(FormSources.from_context(ctx))
    assert not report.errors, report.errors


@pytest.mark.parametrize(
    "factory",
    (DesignContext.slab_serif, DesignContext.bracketed_serif),
)
def test_serif_voice_meets_program_acceptance(factory) -> None:
    """Lint + identity + family gate + L3 + inlined stem serifs (no boolean)."""
    from typekernel.parts.serifs import apply_glyph_serifs

    controls = FormSources.from_context(factory())
    charset = controls.supported
    lint_report = lint_controls(controls)
    assert not lint_report.errors, lint_report.errors
    identity_report = check_identity_controls(controls, charset)
    assert not identity_report.errors, identity_report.errors
    gate_failures = collect_family_gate_failures(controls)
    assert gate_failures == [], gate_failures
    assert nearest_voice_distance(controls) >= L3_VOICE_DISTANCE_THRESHOLD
    assert l3_voice_criteria_met(controls)
    for ch in charset:
        glyph = controls.derive_one(ch)
        assert composed_glyph_hash(glyph) == composed_glyph_hash(
            apply_glyph_serifs(glyph)
        )


def test_bracketed_n_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.bracketed_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("n"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_bracketed_serif_masters_on_vf_stable_charset() -> None:
    """Bracketed voice: full supported charset on the four-master weight ladder."""
    ctx = DesignContext.bracketed_serif()
    controls = FormSources.from_context(ctx)
    charset = controls.supported
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        tuned = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Bracket", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(tuned.derive(charset))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("I"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("E"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive(charset))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("L"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_serif_masters_on_vf_stable_charset() -> None:
    """Slab voice: full supported charset on the four-master weight ladder."""
    ctx = DesignContext.slab_serif()
    controls = FormSources.from_context(ctx)
    charset = controls.supported
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        tuned = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(tuned.derive(charset))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_opening_caps_change_c_and_g_outline() -> None:
    sans = FormSources.from_context(DesignContext.geometric_sans())
    slab = FormSources.from_context(DesignContext.slab_serif())
    for ch in ("c", "C", "G"):
        assert composed_glyph_hash(sans.derive_one(ch)) != composed_glyph_hash(slab.derive_one(ch))


def test_slab_e_opening_changes_outline() -> None:
    sans = FormSources.from_context(DesignContext.geometric_sans())
    slab = FormSources.from_context(DesignContext.slab_serif())
    assert composed_glyph_hash(sans.derive_one("e")) != composed_glyph_hash(slab.derive_one("e"))


def test_slab_s_opening_changes_outline() -> None:
    sans = FormSources.from_context(DesignContext.geometric_sans())
    slab = FormSources.from_context(DesignContext.slab_serif())
    for ch in ("s", "S"):
        assert composed_glyph_hash(sans.derive_one(ch)) != composed_glyph_hash(slab.derive_one(ch))


def test_slab_s_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    for ch in ("s", "S"):
        ref_n = len(
            FormSources.from_context(ctx.tuned(stem=stems[0])).derive_one(ch).solids[0].contours[0].segments
        )
        fonts = []
        for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
            g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one(ch)
            assert len(g.solids[0].contours[0].segments) == ref_n
            font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
            font.add_char(ch, g)
            fonts.append(font)
        masters = [
            Master({"wght": wght}, font)
            for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
        ]
        assert check_masters(masters) == []


def test_slab_cap_cg_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    charset = "CG"
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive(charset))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_t_baked_foot_changes_outline() -> None:
    sans = FormSources.from_context(DesignContext.geometric_sans()).derive_one("t")
    slab = FormSources.from_context(DesignContext.slab_serif()).derive_one("t")
    assert composed_glyph_hash(sans) != composed_glyph_hash(slab)


def test_slab_t_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("t"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_slab_j_and_q_baked_feet_change_outline() -> None:
    sans = FormSources.from_context(DesignContext.geometric_sans())
    slab = FormSources.from_context(DesignContext.slab_serif())
    for ch in ("j", "Q"):
        assert composed_glyph_hash(sans.derive_one(ch)) != composed_glyph_hash(slab.derive_one(ch))


def test_slab_cap_q_masters_interpolate_on_weight_ladder() -> None:
    ctx = DesignContext.slab_serif()
    stems = (70.0, 100.0, 140.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("Q"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("j"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive(charset))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("R"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("B"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("P"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("D"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("A"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("W"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("V"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("U"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("Y"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("X"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("Z"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("K"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("M"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("N"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("T"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("F"))
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
        controls = FormSources.from_context(ctx.tuned(stem=stem))
        font = Font.from_context(ctx, "Slab", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.derive("H"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 500.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []
