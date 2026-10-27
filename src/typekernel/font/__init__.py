"""Font model — glyph set, metrics, cmap, kerning and features for one style.

Sits between the design layers and the compile bridge.

    System ──► Project / @glyph ──► Drawing ──► Glyph.from_drawing ──► Font ──► compile
"""

from __future__ import annotations

from typekernel.font.font import Font
from typekernel.font.glyph import (
    Anchor,
    Component,
    Glyph,
    glyph_name_for_char,
    normalize_winding,
    notdef_glyph_from_system,
    space_glyph_from_system,
)
from typekernel.font.info import FontInfo, alignment_zones_from_system
from typekernel.font.kerning import (
    ClassKernPair,
    ClassKernTable,
    KernClass,
    KernPair,
    KernTable,
)
from typekernel.font.masters import AXIS_NAMES, Master, axis_ranges, check_masters

__all__ = [
    "AXIS_NAMES",
    "Anchor",
    "ClassKernPair",
    "ClassKernTable",
    "Component",
    "Font",
    "FontInfo",
    "Glyph",
    "KernClass",
    "KernPair",
    "KernTable",
    "Master",
    "alignment_zones_from_system",
    "axis_ranges",
    "check_masters",
    "glyph_name_for_char",
    "normalize_winding",
    "notdef_glyph_from_system",
    "space_glyph_from_system",
]
