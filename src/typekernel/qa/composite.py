"""Flatten font-layer component glyphs for parts-layer QA (lint, samples)."""

from __future__ import annotations

from typekernel.font import Font
from typekernel.geo.outline import Outline
from typekernel.parts.compose import ComposedGlyph, translate_outline

__all__ = ["composed_glyph_from_font"]


def composed_glyph_from_font(font: Font, glyph_name: str) -> ComposedGlyph:
    """Bake ``glyph_name`` (base + mark components) into one :class:`ComposedGlyph`."""
    ctx = font.context
    if ctx is None:
        raise ValueError("font.context is required")
    glyph = font[glyph_name]
    if not glyph.components:
        lone = (glyph.outline,) if glyph.outline.contours else ()
        return ComposedGlyph(lone, (), glyph.advance, ctx)
    solids: list[Outline] = []
    for comp in glyph.components:
        sub = font[comp.base]
        dx, dy = comp.transform[4], comp.transform[5]
        outline = translate_outline(sub.outline, dx, dy)
        if outline.contours:
            solids.append(outline)
    return ComposedGlyph(tuple(solids), (), glyph.advance, ctx)
