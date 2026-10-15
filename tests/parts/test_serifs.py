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
