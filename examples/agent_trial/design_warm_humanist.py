"""Reference agent trial for brief-1 (TK-502): warm humanist UI sans.

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

__all__ = ["controls"]


def controls() -> Controls:
    """Regular master for brief-1 (pair with ``with_stem_relief()`` for Bold)."""
    ctx = DesignContext.humanist_sans().tuned(
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
    return (
        Controls.from_context(ctx)
        .tuned_glyph("f", arm=0.62)
        .tuned_glyph("t", arm=0.45)
        .tuned_glyph("s", top_scale=0.82)
        .tuned_glyph("e", bar_raise=0.35)
        .tuned_glyph("K", width=1.08)
        .tuned_glyph("R", leg_at=0.90)
    )
