"""Helpers: Drawing → font.Glyph (ARCHITECTURE.md §9.7a)."""

from __future__ import annotations

from typekernel.draw import Drawing
from typekernel.font.glyph import Glyph
from typekernel.geo.outline import bounds

__all__ = ["advance_from_drawing", "drawing_to_glyph"]


def advance_from_drawing(drawing: Drawing) -> float:
    """BBox width of the drawing outline; ``0.0`` when the outline is empty."""
    outline = drawing.outline()
    if not outline.contours or not any(c.segments for c in outline.contours):
        return 0.0
    min_x, _min_y, max_x, _max_y = bounds(outline)
    return float(max_x - min_x)


def drawing_to_glyph(
    name: str,
    drawing: Drawing,
    *,
    advance: float,
    unicodes: tuple[int, ...] = (),
) -> Glyph:
    """Wrap a Drawing's contours as a ``font.Glyph``."""
    return Glyph(
        name=name,
        outline=drawing.outline(),
        advance=advance,
        unicodes=unicodes,
    )
