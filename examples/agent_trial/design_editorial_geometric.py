"""Reference agent trial for brief-2 (TK-502): editorial geometric sans.

Single-storey ``a``/``g`` via ``Style``; sharper ``roundness`` + ``tuned_glyph``.
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style

__all__ = ["controls"]


def controls() -> Controls:
    ctx = DesignContext.geometric_sans().tuned(
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
    return (
        Controls.from_context(ctx)
        .tuned_glyph("f", arm=0.58)
        .tuned_glyph("s", top_scale=0.84)
        .tuned_glyph("K", width=1.06)
    )
