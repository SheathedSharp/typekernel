"""Slab serif voice (serif voices): Regular + Bold from ``slab_serif()``."""

from __future__ import annotations

from typekernel.parts import FormSources, DesignContext
from typekernel.parts.control import f_from_n, t_from_n

FAMILY_NAME = "Typekernel Slab"
PRESET_NAME = "slab_serif"
BRIEF_SENTENCE = "Slab nHIL — the quick brown fox jumps over 0123456789."


def baseline_controls() -> FormSources:
    return FormSources.from_context(DesignContext.slab_serif())


def _voice(stem: float, *, relief: bool) -> FormSources:
    ctx = DesignContext.slab_serif().tuned(stem=stem)
    controls = FormSources.from_context(ctx)
    # arm 0.75 keeps ``f`` segment count stable on the four-master VF ladder (0.80 drifts).
    controls = controls.with_glyph("f", lambda n, o, c: f_from_n(n, c, arm=0.75))
    controls = controls.with_glyph("t", lambda n, o, c: t_from_n(n, c, arm=0.56))
    if relief:
        controls = controls.with_stem_relief()
    return controls


def design_controls() -> FormSources:
    return _voice(DesignContext.slab_serif().stem, relief=False)


def design_light() -> FormSources:
    return _voice(82.0, relief=False)


def design_bold() -> FormSources:
    return _voice(118.0, relief=True)
