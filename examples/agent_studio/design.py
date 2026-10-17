"""Agent-authored L0 trial — edit this file; typekernel is the library, not the brief.

Human designer order for a trial (not a family):
  brief → named preset → control glyphs → DesignSequence body unlock →
  documented delta → weak letters → proof.

``BRIEF_SENTENCE`` is the second specimen only. Pass/fail uses
``typekernel.qa.sentence_gate.AGENT_SENTENCE``. Do not change that sentence
to make the gate pass.

Full family (Light/Bold or a VF) belongs in ``examples/<family>/build_*.py``.
Start from ``examples/agent_family/``.
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.control import f_from_n, t_from_n
from typekernel.qa.design_sequence import DesignSequence

# --- Brief (record intent before touching numbers) ---
# Voice: humanist UI sans. This trial stays on the preset's topology.
# Body letters unlock via DesignSequence; build_all is compose-time only.
# Weights: Regular only.
FAMILY_NAME = "Agent Studio Humanist"
PRESET_NAME = "humanist_sans"
FOCUS_GLYPHS = "n o a s e f t r I"
BRIEF_SENTENCE = "Typekernel fonts think in families, not lonely glyphs."


def baseline_controls() -> Controls:
    """Unmodified preset. The trial must not worsen its gap ratio or G1."""
    return Controls.from_context(DesignContext.humanist_sans())


def design_controls() -> Controls:
    """L0 sheet: one documented proportion delta and two weak-glyph masters.

    Preset ``sidebearing_ratio`` is 0.10. Opening it to 0.11 is a rhythm
    decision after the control ``n`` / ``o``, not a free stem number.
    ``f`` and ``t`` are single-glyph masters (library builders, explicit arms).
    """
    ctx = DesignContext.humanist_sans().tuned(sidebearing_ratio=0.11)
    controls = Controls.from_context(ctx)
    controls = controls.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.82))
    controls = controls.with_glyph("t", lambda n, o, c: t_from_n(n, c, arm=0.58))
    return controls


def unlock_body_sequence(controls: Controls | None = None) -> DesignSequence:
    """Required body gate: one glyph → style-check → unlock (no ungated batch)."""
    sheet = controls if controls is not None else design_controls()
    return sheet.unlock_body()  # type: ignore[return-value]
