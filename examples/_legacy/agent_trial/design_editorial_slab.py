"""Reference agent trial for brief-2 (agent trial): editorial slab serif.

Starts from ``slab_serif()``; ``roundness`` / ``tracking`` + ``tuned_glyph`` on
documented fields. ``f``/``t`` ``with_glyph`` matches ``examples/slab_serif``
for VF-stable segment counts.

Run::

    PYTHONPATH=src python examples/agent_trial/build_reference_family.py \\
        --brief brief-2 --variant slab --out artifacts/trials/editorial-slab-family
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.control import f_from_n, t_from_n

FAMILY_NAME = "Trial Editorial Slab"
_BOLD_STEM = 120.0

__all__ = [
    "FAMILY_NAME",
    "baseline_controls",
    "controls",
    "design_bold",
]


def baseline_controls() -> Controls:
    return Controls.from_context(DesignContext.slab_serif())


def _voice(stem: float, *, relief: bool) -> Controls:
    ctx = DesignContext.slab_serif().tuned(
        stem=stem,
        roundness=0.24,
        tracking=0.015,
    )
    sheet = (
        Controls.from_context(ctx)
        .with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.75))
        .with_glyph("t", lambda n, o, c: t_from_n(n, c, arm=0.56))
        .tuned_glyph("s", top_scale=0.85)
        .tuned_glyph("e", bar_raise=0.34)
        .tuned_glyph("K", width=1.03)
    )
    return sheet.with_stem_relief() if relief else sheet


def controls() -> Controls:
    return _voice(DesignContext.slab_serif().stem, relief=False)


def design_bold() -> Controls:
    return _voice(_BOLD_STEM, relief=True)
