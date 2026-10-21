"""Bracketed serif voice (serif voices): Regular + Bold from ``bracketed_serif()``."""

from __future__ import annotations

from typekernel.parts import FormSources, DesignContext
from typekernel.parts.control import f_from_n, t_from_n

FAMILY_NAME = "Typekernel Bracket"
PRESET_NAME = "bracketed_serif"
BRIEF_SENTENCE = "Bracket nHIL — the quick brown fox jumps over 0123456789."


def baseline_controls() -> FormSources:
    return _voice(DesignContext.bracketed_serif().stem, relief=False)


def _voice(stem: float, *, relief: bool) -> FormSources:
    ctx = DesignContext.bracketed_serif().tuned(stem=stem)
    controls = FormSources.from_context(ctx)
    controls = controls.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.75))
    controls = controls.with_glyph("t", lambda n, o, c: t_from_n(n, c, arm=0.56))
    if relief:
        controls = controls.with_stem_relief()
    return controls


def design_controls() -> FormSources:
    return _voice(DesignContext.bracketed_serif().stem, relief=False)


def design_light() -> FormSources:
    return _voice(58.0, relief=False)


def design_bold() -> FormSources:
    return _voice(118.0, relief=True)
