"""Warm humanist reference voice (Usage A sugar via FormSources)."""

from __future__ import annotations

from typekernel.parts import DesignContext, FormSources
from typekernel.parts.style import Style

FAMILY_NAME = "Trial Warm Humanist"
_BOLD_STEM = 120.0

__all__ = [
    "FAMILY_NAME",
    "baseline_controls",
    "controls",
    "design_bold",
]


def baseline_controls() -> FormSources:
    return FormSources.from_context(DesignContext.humanist_sans())


def _voice(stem: float, *, relief: bool) -> FormSources:
    ctx = DesignContext.humanist_sans().tuned(
        stem=stem,
        roundness=0.40,
        terminal_style="ball",
        style=Style(
            a_form="single",
            g_form="single",
            l_tail="tailed",
            y_tail="curved",
            t_cut="slanted",
            i_dot="square",
        ),
    )
    sheet = (
        FormSources.from_context(ctx)
        .tuned_glyph("f", arm=0.62)
        .tuned_glyph("t", arm=0.45)
        .tuned_glyph("s", top_scale=0.82)
        .tuned_glyph("e", bar_raise=0.35)
        .tuned_glyph("K", width=1.05)
        .tuned_glyph("R", leg_at=0.90)
    )
    return sheet.with_stem_relief() if relief else sheet


def controls() -> FormSources:
    return _voice(DesignContext.humanist_sans().stem, relief=False)


def design_bold() -> FormSources:
    return _voice(_BOLD_STEM, relief=True)
