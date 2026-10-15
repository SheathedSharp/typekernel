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


# Caps with anchor slab feet + ``j``/``t`` still drift segment counts on the ladder.
_SLAB_VF_STABLE_EXCLUDE = "ABDGKPQRUVWXYZjt"  # baked: C E F H I J L M N O S T


def test_slab_serif_masters_on_vf_stable_charset() -> None:
    """Slab voice: lint-clean charset minus known VF-unstable cap hook letters."""
    ctx = DesignContext.slab_serif()
    controls = Controls.from_context(ctx)
    charset = "".join(ch for ch in controls.supported if ch not in _SLAB_VF_STABLE_EXCLUDE)
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


def test_slab_t_masters_interpolate_on_weight_ladder() -> None:
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
