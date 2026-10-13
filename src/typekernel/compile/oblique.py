"""Oblique masters by shearing outlines (``slnt`` axis), not true italic."""

from __future__ import annotations

from dataclasses import replace

from typekernel.axes.slant import ObliqueTransform
from typekernel.font import Font, Glyph

__all__ = ["oblique_font"]


def _shear_glyph(glyph: Glyph, shear: ObliqueTransform) -> Glyph:
    return replace(glyph, outline=shear.apply(glyph.outline))


def oblique_font(font: Font, angle_degrees: float, *, style_name: str = "Oblique") -> Font:
    """Return a new :class:`Font` with every outline sheared."""
    shear = ObliqueTransform(angle_degrees)
    info = replace(
        font.info,
        style_name=style_name,
        extra={**font.info.extra, "italicAngle": -angle_degrees},
    )
    out = Font(info=info, context=font.context)
    for g in font:
        out.add_glyph(_shear_glyph(g, shear))
    out.groups = dict(font.groups)
    out.kerning = dict(font.kerning)
    out.features = font.features
    return out
