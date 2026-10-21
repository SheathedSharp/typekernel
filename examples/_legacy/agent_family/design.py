"""L2 family sheet. Replace the TODOs; do not grow this inside agent_studio.

Regular is the voice you compare to the unmodified preset.
Light and Bold are separate masters (new stems), not a stroke expand.
Bold calls ``with_stem_relief()``. Do not compare Bold's gap ratio to Regular's preset.

Each master must pass ``Controls.unlock_body`` (DesignSequence) before compose;
``build_all`` in ``build_family.py`` is compile-time derivation only.
"""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext
from typekernel.parts.control import f_from_n, t_from_n
from typekernel.qa.design_sequence import DesignSequence

# TODO: rename the family and rewrite the brief before calling this a release.
FAMILY_NAME = "Agent Family Humanist"
PRESET_NAME = "humanist_sans"
BRIEF_SENTENCE = "Typekernel fonts think in families, not lonely glyphs."

# Preset stem is 70. These are starting masters, not finished weights.
_LIGHT_STEM = 48.0
_BOLD_STEM = 140.0


def baseline_controls() -> Controls:
    """Unmodified preset for the Regular voice only."""
    return Controls.from_context(DesignContext.humanist_sans())


def _voice(stem: float, *, relief: bool) -> Controls:
    # TODO: after design_review on Regular, retune this voice per master.
    # One documented delta from the preset (sidebearing 0.10 → 0.11).
    ctx = DesignContext.humanist_sans().tuned(stem=stem, sidebearing_ratio=0.11)
    controls = Controls.from_context(ctx)
    controls = controls.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.82))
    controls = controls.with_glyph("t", lambda n, o, c: t_from_n(n, c, arm=0.58))
    if relief:
        controls = controls.with_stem_relief()
    return controls


def design_controls() -> Controls:
    """Regular master."""
    return _voice(DesignContext.humanist_sans().stem, relief=False)


def design_light() -> Controls:
    """Light master: thinner stem, own control sheet."""
    return _voice(_LIGHT_STEM, relief=False)


def design_bold() -> Controls:
    """Bold master: heavier stem plus counter relief."""
    return _voice(_BOLD_STEM, relief=True)


def unlock_body_sequence(controls: Controls) -> DesignSequence:
    """Designer-order body gate for one master (required before compose)."""
    return controls.unlock_body()  # type: ignore[return-value]
