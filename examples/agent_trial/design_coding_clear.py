"""Reference agent trial for brief-3 (TK-502): coding / UI clear sans.

Full ASCII punctuation charset from ``code_clear``; ``Style`` + terminal ball.
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style

FAMILY_NAME = "Trial Coding Clear"
_BOLD_STEM = 120.0

__all__ = [
    "FAMILY_NAME",
    "baseline_controls",
    "controls",
    "design_bold",
]


def baseline_controls() -> Controls:
    return Controls.from_context(DesignContext.code_clear())


def _voice(stem: float, *, relief: bool) -> Controls:
    ctx = DesignContext.code_clear().tuned(
        stem=stem,
        roundness=0.25,
        terminal_style="ball",
        style=Style(
            a_form="single",
            g_form="single",
            l_tail="hooked",
            t_cut="angled",
            i_dot="square",
        ),
    )
    sheet = (
        Controls.from_context(ctx)
        .tuned_glyph("f", arm=0.55)
        .tuned_glyph("t", arm=0.42)
        .tuned_glyph("s", top_scale=0.86)
    )
    return sheet.with_stem_relief() if relief else sheet


def controls() -> Controls:
    return _voice(DesignContext.code_clear().stem, relief=False)


def design_bold() -> Controls:
    return _voice(_BOLD_STEM, relief=True)
