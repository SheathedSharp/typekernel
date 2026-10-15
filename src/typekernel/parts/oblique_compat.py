"""Oblique pre-splits for bowl-like glyphs (TK-402, VF-safe subset)."""

from __future__ import annotations

import math

from typekernel.geo.extrema import outline_oblique_compat_splits
from typekernel.parts.compose import ComposedGlyph

# Branching-arch italics (TK-403) diverge in segment topology after oblique splits.
# ``e`` counter splits diverge under ``with_stem_relief`` (wght axis); arch letters
# use TK-403 branching (``vf_compat_stem``) instead.
OBLIQUE_COMPAT_EXCLUDE = frozenset("efhmnru")

__all__ = [
    "OBLIQUE_COMPAT_EXCLUDE",
    "apply_oblique_compat_glyph",
    "oblique_compat_charset",
]


def oblique_compat_charset(supported: str | tuple[str, ...] | frozenset[str]) -> frozenset[str]:
    """Glyphs where upright split + italic split+slant share segment counts."""
    if isinstance(supported, str):
        chars = frozenset(supported)
    elif isinstance(supported, frozenset):
        chars = supported
    else:
        chars = frozenset(supported)
    return chars - OBLIQUE_COMPAT_EXCLUDE


def apply_oblique_compat_glyph(
    glyph: ComposedGlyph,
    angle_deg: float,
    *,
    slant: bool,
) -> ComposedGlyph:
    """Pre-split for oblique axis extrema; optionally apply construct slant."""
    shear = math.tan(math.radians(angle_deg))
    split_glyph = ComposedGlyph(
        tuple(outline_oblique_compat_splits(s, shear) for s in glyph.solids),
        tuple(outline_oblique_compat_splits(h, shear) for h in glyph.holes),
        glyph.advance,
        glyph.context,
        anchors=glyph.anchors,
        design=glyph.design,
    )
    if slant:
        from typekernel.parts.italic import slant_composed_glyph

        return slant_composed_glyph(split_glyph, angle_deg)
    return split_glyph
