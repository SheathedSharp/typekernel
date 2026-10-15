"""Slab serif voice (TK-306): Regular + Bold from ``slab_serif()``."""

from __future__ import annotations

from typekernel.parts import Controls, DesignContext

FAMILY_NAME = "Typekernel Slab"
PRESET_NAME = "slab_serif"


def baseline_controls() -> Controls:
    return Controls.from_context(DesignContext.slab_serif())


def design_controls() -> Controls:
    return baseline_controls()


def design_light() -> Controls:
    return Controls.from_context(DesignContext.slab_serif().tuned(stem=82.0))


def design_bold() -> Controls:
    return Controls.from_context(DesignContext.slab_serif().tuned(stem=118.0)).with_stem_relief()
