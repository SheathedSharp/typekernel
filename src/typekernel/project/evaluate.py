"""Helpers: Drawing → font.Glyph (ARCHITECTURE.md Project / @glyph / Master)."""

from __future__ import annotations

from fontTools.agl import AGL2UV

from typekernel.draw import Drawing
from typekernel.font.glyph import Glyph
from typekernel.geo.outline import bounds

__all__ = ["advance_from_drawing", "drawing_to_glyph", "unicodes_for_glyph_name"]


def advance_from_drawing(drawing: Drawing) -> float:
    """BBox width of the drawing outline; ``0.0`` when the outline is empty."""
    outline = drawing.outline()
    if not outline.contours or not any(c.segments for c in outline.contours):
        return 0.0
    min_x, _min_y, max_x, _max_y = bounds(outline)
    return float(max_x - min_x)


def unicodes_for_glyph_name(name: str) -> tuple[int, ...]:
    """Map an AGL / single-character production name to codepoints.

    Synthetic names (``syn.arch``, ``fixture.stem``) yield an empty tuple so
    kernel fixtures stay unmapped. Letter names used in project starters
    (``n``, ``O``, …) resolve via fontTools AGL.
    """
    cp = AGL2UV.get(name)
    if cp is not None:
        return (int(cp),)
    if len(name) == 1:
        return (ord(name),)
    return ()


def drawing_to_glyph(
    name: str,
    drawing: Drawing,
    *,
    advance: float,
    unicodes: tuple[int, ...] | None = None,
) -> Glyph:
    """Wrap a Drawing's contours as a ``font.Glyph``.

    When ``unicodes`` is omitted, derive from ``name`` via
    :func:`unicodes_for_glyph_name`.
    """
    if unicodes is None:
        unicodes = unicodes_for_glyph_name(name)
    return Glyph.from_drawing(name, drawing, advance=advance, unicodes=unicodes)
