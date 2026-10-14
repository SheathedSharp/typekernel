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
