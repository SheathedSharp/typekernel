"""Glyph parts — compose letters from shared primitives (Three.js metaphor).

Use one :class:`DesignContext` for a whole word or family, build letters from
:mod:`typekernel.parts.primitives`, transform with :mod:`typekernel.parts.transforms`,
space with :mod:`typekernel.parts.metrics`, and assemble with :class:`GlyphAssembler`.

Boolean union / difference of overlapping solids needs the optional extra::

    pip install "typekernel[boolean]"

Coding agents: see ``examples/agent_catalog/`` for a one-liner index of every
public constructor in this package.
"""

from __future__ import annotations

from typekernel.parts.compose import (
    ComposedGlyph,
    GlyphAssembler,
    translate_outline,
    try_difference,
    try_intersection,
    try_union,
)
from typekernel.parts.context import DesignContext
from typekernel.parts.latin import (
    LETTER_BUILDERS,
    build_letter,
    build_word,
    letter_a,
    letter_c,
    letter_e,
    letter_h,
    letter_i,
    letter_j,
    letter_l,
    letter_n,
    letter_o,
    letter_s,
    letter_u,
    letter_y,
    letter_z,
    word_zayju,
)
from typekernel.parts.metrics import (
    KernPair,
    KernTable,
    default_sans_kern,
    layout_glyphs,
    sidebearing_for_width,
)
from typekernel.parts.primitives import (
    apply_ink_trap,
    arch,
    bowl,
    capsule,
    counter,
    crossbar,
    crotch_join,
    crotch_opener,
    diagonal_stem,
    fillet_pad,
    hook_terminal,
    horizontal_bar,
    ink_trap,
    rounded_rect,
    serif_bracket,
    shoulder,
    smooth_hook,
    stroke_polyline,
    terminal_ball,
    terminal_sheared,
    tittle,
    u_bowl,
    vertical_stem,
    wedge,
)
from typekernel.parts.transforms import (
    mirror_x,
    mirror_y,
    rotate,
    scale,
    translate,
)

__all__ = [
    "LETTER_BUILDERS",
    "ComposedGlyph",
    "DesignContext",
    "GlyphAssembler",
    "KernPair",
    "KernTable",
    "apply_ink_trap",
    "arch",
    "bowl",
    "build_letter",
    "build_word",
    "capsule",
    "counter",
    "crossbar",
    "crotch_join",
    "crotch_opener",
    "default_sans_kern",
    "diagonal_stem",
    "fillet_pad",
    "hook_terminal",
    "horizontal_bar",
    "ink_trap",
    "layout_glyphs",
    "letter_a",
    "letter_c",
    "letter_e",
    "letter_h",
    "letter_i",
    "letter_j",
    "letter_l",
    "letter_n",
    "letter_o",
    "letter_s",
    "letter_u",
    "letter_y",
    "letter_z",
    "mirror_x",
    "mirror_y",
    "rotate",
    "rounded_rect",
    "scale",
    "serif_bracket",
    "shoulder",
    "sidebearing_for_width",
    "smooth_hook",
    "stroke_polyline",
    "terminal_ball",
    "terminal_sheared",
    "tittle",
    "translate",
    "translate_outline",
    "try_difference",
    "try_intersection",
    "try_union",
    "u_bowl",
    "vertical_stem",
    "wedge",
    "word_zayju",
]
