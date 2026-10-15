"""TK-305: Style options lint clean on touched glyphs and VF-compatible masters."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Master, check_masters
from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style
from typekernel.qa.lint import lint_controls

_STYLE_LINT_CASES: tuple[tuple[Style, str], ...] = (
    (Style(i_dot="square"), "i"),
    (Style(i_dot="diamond"), "i"),
    (Style(a_form="double"), "a"),
    (Style(g_form="double"), "g"),
    (Style(l_tail="tailed"), "l"),
    (Style(y_tail="curved"), "y"),
    (Style(t_cut="slanted"), "t"),
)


@pytest.mark.parametrize(("style", "chars"), _STYLE_LINT_CASES)
def test_style_option_lint_clean_on_geometric(style: Style, chars: str) -> None:
    controls = Controls.from_context(DesignContext.geometric_sans(), style=style)
    report = lint_controls(controls, chars)
    assert not report.errors, report.errors


def test_styled_masters_interpolate_across_weight_ladder() -> None:
    """Non-topology Style switches must keep point compatibility for VF."""
    ctx = DesignContext.code_clear()
    style = Style(l_tail="tailed", y_tail="curved", t_cut="slanted", i_dot="diamond")
    charset = "nolhijty"  # skip a/g (topology changes with relief on double forms)
    regular = Controls.from_context(ctx.tuned(stem=86), style=style)
    bold = Controls.from_context(ctx.tuned(stem=140), style=style).with_stem_relief()
    reg_font = Font.from_context(ctx, "Style Sans", "Regular", weight_class=400)
    reg_font.add_chars(regular.build_all(charset))
    bold_font = Font.from_context(ctx, "Style Sans", "Bold", weight_class=700)
    bold_font.add_chars(bold.build_all(charset))
    masters = [Master({"wght": 400.0}, reg_font), Master({"wght": 700.0}, bold_font)]
    assert check_masters(masters) == []


def test_double_g_form_masters_interpolate_on_weight_ladder() -> None:
    """``g_form=double`` keeps point topology across a wide stem span."""
    ctx = DesignContext.code_clear()
    style = Style(g_form="double")
    stems = (70.0, 110.0, 150.0, 180.0)
    fonts = []
    for stem, wght in zip(stems, (300.0, 400.0, 600.0, 700.0), strict=True):
        controls = Controls.from_context(ctx.tuned(stem=stem), style=style)
        if stem >= 150.0:
            controls = controls.with_stem_relief()
        font = Font.from_context(ctx, "Style Sans", f"W{int(wght)}", weight_class=int(wght))
        font.add_chars(controls.build_all("g"))
        fonts.append(font)
    masters = [
        Master({"wght": wght}, font)
        for wght, font in zip((300.0, 400.0, 600.0, 700.0), fonts, strict=True)
    ]
    assert check_masters(masters) == []


def test_double_a_form_masters_interpolate_light_to_medium() -> None:
    """``a_form=double`` interpolates on code_clear between stem 86 and 100."""
    ctx = DesignContext.code_clear()
    style = Style(a_form="double")
    regular = Controls.from_context(ctx.tuned(stem=86.0), style=style)
    medium = Controls.from_context(ctx.tuned(stem=100.0), style=style)
    reg_font = Font.from_context(ctx, "Style Sans", "Regular", weight_class=400)
    reg_font.add_chars(regular.build_all("a"))
    med_font = Font.from_context(ctx, "Style Sans", "Medium", weight_class=500)
    med_font.add_chars(medium.build_all("a"))
    masters = [Master({"wght": 400.0}, reg_font), Master({"wght": 500.0}, med_font)]
    assert check_masters(masters) == []


@pytest.mark.parametrize(
    "style",
    (
        Style(a_form="double"),
        Style(g_form="double"),
        Style(l_tail="tailed", y_tail="curved", t_cut="slanted", i_dot="diamond"),
    ),
)
def test_style_option_lint_clean_on_full_supported(style: Style) -> None:
    controls = Controls.from_context(DesignContext.code_clear(), style=style)
    report = lint_controls(controls)
    assert not report.errors, report.errors
