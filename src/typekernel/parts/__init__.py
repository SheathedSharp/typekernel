"""Glyph parts — compose letters from shared primitives (Three.js metaphor).

Use one :class:`DesignContext` for a whole word or family, build letters from
:mod:`typekernel.parts.primitives`, and assemble with :class:`GlyphAssembler`.

Boolean union of overlapping solids needs the optional extra::

    pip install "typekernel[boolean]"
"""

from __future__ import annotations

from typekernel.parts.compose import ComposedGlyph, GlyphAssembler, translate_outline
from typekernel.parts.context import DesignContext
from typekernel.parts.latin import letter_a, letter_j, letter_u, letter_y, letter_z, word_zayju
from typekernel.parts.primitives import (
    arch,
    bowl,
    counter,
    diagonal_stem,
    hook_terminal,
    horizontal_bar,
    rounded_rect,
    tittle,
    u_bowl,
    vertical_stem,
)

__all__ = [
    "ComposedGlyph",
    "DesignContext",
    "GlyphAssembler",
    "arch",
    "bowl",
    "counter",
    "diagonal_stem",
    "hook_terminal",
    "horizontal_bar",
    "letter_a",
    "letter_j",
    "letter_u",
    "letter_y",
    "letter_z",
    "rounded_rect",
    "tittle",
    "translate_outline",
    "u_bowl",
    "vertical_stem",
    "word_zayju",
]
