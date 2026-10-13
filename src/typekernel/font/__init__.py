"""Font model — glyph set, metrics, cmap, kerning and features for one style.

Sits between the design layers and the compile bridge::

    DesignContext ──► parts / control glyphs ──► Font ──► compile (UFO → OTF/TTF)

Typical use::

    from typekernel.compile import build_font
    from typekernel.font import Font
    from typekernel.parts import DesignContext, build_n, build_o

    ctx = DesignContext.code_clear()
    font = Font.from_context(ctx, "My Sans")      # .notdef + space included
    font.add_chars({"n": build_n(ctx), "o": build_o(ctx)})
    build_font(font, "build/")                    # UFO + OTF + TTF
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
    space_glyph,
)
from typekernel.font.info import FontInfo, alignment_zones

__all__ = [
    "Anchor",
    "Component",
    "Font",
    "FontInfo",
    "Glyph",
    "alignment_zones",
    "glyph_name_for_char",
    "normalize_winding",
    "notdef_glyph",
    "space_glyph",
]
