"""Reference agent trial for brief-1 (agent trial): warm humanist UI sans.

Not a preset snapshot: ``Style`` + ``terminal_style`` + context ``roundness``
+ ``tuned_glyph`` on documented fields. Snapshot must keep
``weight_ladder_r8_failures == 0`` and ``voice_distance`` ≥ L3 (0.35).

Run::

    PYTHONPATH=src python examples/agent_trial/snapshot_design.py \\
        --brief brief-1 --out artifacts/trials/my-run
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.style import Style

FAMILY_NAME = "Trial Warm Humanist"
_BOLD_STEM = 120.0

__all__ = [
    "FAMILY_NAME",
    "baseline_controls",
    "controls",
    "design_bold",
]


def baseline_controls() -> Controls:
    """Unmodified preset (Regular comparison baseline for ``design_review``)."""
    return Controls.from_context(DesignContext.humanist_sans())


def _voice(stem: float, *, relief: bool) -> Controls:
    ctx = DesignContext.humanist_sans().tuned(
        stem=stem,
        roundness=0.40,
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
        .tuned_glyph("f", arm=0.62)
        .tuned_glyph("t", arm=0.45)
        .tuned_glyph("s", top_scale=0.82)
        .tuned_glyph("e", bar_raise=0.35)
        .tuned_glyph("K", width=1.05)
        .tuned_glyph("R", leg_at=0.90)
    )
    return sheet.with_stem_relief() if relief else sheet


def controls() -> Controls:
    """Regular master for brief-1."""
    return _voice(DesignContext.humanist_sans().stem, relief=False)


def design_bold() -> Controls:
    """Bold master (separate stem + ``with_stem_relief()``)."""
    return _voice(_BOLD_STEM, relief=True)
