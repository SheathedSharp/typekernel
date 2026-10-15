"""Reference agent trial for brief-3 (TK-502): coding / UI clear sans.

Full ASCII punctuation charset from ``code_clear``; ``Style`` + terminal ball.
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style

__all__ = ["controls"]


def controls() -> Controls:
    ctx = DesignContext.code_clear().tuned(
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
    return (
        Controls.from_context(ctx)
        .tuned_glyph("f", arm=0.55)
        .tuned_glyph("t", arm=0.42)
        .tuned_glyph("s", top_scale=0.86)
    )
