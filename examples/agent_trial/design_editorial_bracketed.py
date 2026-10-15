"""Reference agent trial for brief-2 (TK-502): editorial bracketed serif.

Starts from ``bracketed_serif()`` (default stem 70); light ``tracking`` +
``tuned_glyph``. ``f``/``t`` ``with_glyph`` matches ``examples/bracketed_serif``.

Run::

    PYTHONPATH=src python examples/agent_trial/build_reference_family.py \\
        --brief brief-2 --variant bracketed --out artifacts/trials/editorial-bracket-family
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.control import f_from_n, t_from_n

FAMILY_NAME = "Trial Editorial Bracket"
_BOLD_STEM = 118.0

__all__ = [
    "FAMILY_NAME",
    "baseline_controls",
    "controls",
    "design_bold",
]


def baseline_controls() -> Controls:
    return Controls.from_context(DesignContext.bracketed_serif())


def _voice(stem: float, *, relief: bool) -> Controls:
    ctx = DesignContext.bracketed_serif().tuned(stem=stem, tracking=0.012)
    sheet = (
        Controls.from_context(ctx)
        .with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.75))
        .with_glyph("t", lambda n, o, c: t_from_n(n, c, arm=0.56))
        .tuned_glyph("s", top_scale=0.85)
        .tuned_glyph("e", bar_raise=0.32)
        .tuned_glyph("K", width=1.02)
    )
    return sheet.with_stem_relief() if relief else sheet


def controls() -> Controls:
    return _voice(DesignContext.bracketed_serif().stem, relief=False)


def design_bold() -> Controls:
    return _voice(_BOLD_STEM, relief=True)
