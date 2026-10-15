"""Reference agent trial for brief-2 (TK-502): editorial geometric sans.

Single-storey ``a``/``g`` via ``Style``; sharper ``roundness`` + ``tuned_glyph``.
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style

FAMILY_NAME = "Trial Editorial Geometric"
_BOLD_STEM = 120.0

__all__ = [
    "FAMILY_NAME",
    "baseline_controls",
    "controls",
    "design_bold",
]


def baseline_controls() -> Controls:
    return Controls.from_context(DesignContext.geometric_sans())


def _voice(stem: float, *, relief: bool) -> Controls:
    ctx = DesignContext.geometric_sans().tuned(
        stem=stem,
        roundness=0.38,
        terminal_style="ball",
        style=Style(
            a_form="single",
            g_form="single",
            l_tail="hooked",
            y_tail="curved",
            t_cut="angled",
            i_dot="square",
        ),
    )
    sheet = (
        Controls.from_context(ctx)
        .tuned_glyph("f", arm=0.58)
        .tuned_glyph("s", top_scale=0.84)
        .tuned_glyph("K", width=1.06)
    )
    return sheet.with_stem_relief() if relief else sheet


def controls() -> Controls:
    return _voice(DesignContext.geometric_sans().stem, relief=False)


def design_bold() -> Controls:
    return _voice(_BOLD_STEM, relief=True)
