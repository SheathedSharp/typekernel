"""Font model — glyph set, metrics, cmap, kerning and features for one style.

Sits between the design layers and the compile bridge.

New (ARCHITECTURE.md M2) path::

    System ──► Project / @glyph ──► Drawing ──► Glyph.from_drawing ──► Font ──► compile

Legacy path (kept until M4)::

    DesignContext ──► parts / control glyphs ──► Font.from_context ──► compile
"""

from __future__ import annotations

from typekernel.font.font import Font
from typekernel.font.glyph import (
    Anchor,
    Component,
    Glyph,
    glyph_name_for_char,
    normalize_winding,
    notdef_glyph,
    notdef_glyph_from_system,
    space_glyph,
    space_glyph_from_system,
)
from typekernel.font.info import FontInfo, alignment_zones, alignment_zones_from_system
from typekernel.font.masters import AXIS_NAMES, Master, axis_ranges, check_masters

__all__ = [
    "AXIS_NAMES",
    "Anchor",
    "Component",
    "Font",
    "FontInfo",
    "Glyph",
    "Master",
    "alignment_zones",
    "alignment_zones_from_system",
    "axis_ranges",
    "check_masters",
    "glyph_name_for_char",
    "normalize_winding",
    "notdef_glyph",
    "notdef_glyph_from_system",
    "space_glyph",
    "space_glyph_from_system",
]
