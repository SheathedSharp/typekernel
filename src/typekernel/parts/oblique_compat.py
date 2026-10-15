"""Oblique pre-splits for bowl-like glyphs (TK-402, VF-safe subset)."""

from __future__ import annotations

import math

from typekernel.geo.extrema import (
    outline_oblique_compat_splits,
    outline_with_axis_extrema_on_curve,
)
from typekernel.parts.compose import ComposedGlyph

# ``e`` stays on plain construct slant: oblique pre-splits change counter segment
# counts when ``with_stem_relief()`` bold masters pair with upright VF splits (TK-402).
OBLIQUE_COMPAT_EXCLUDE = frozenset("e")
# Branching ``m`` / ``u`` need on-curve axis extrema before oblique pre-split (TK-402).
OBLIQUE_PRE_EXTREMA = frozenset("mu")

__all__ = [
    "OBLIQUE_COMPAT_EXCLUDE",
    "OBLIQUE_PRE_EXTREMA",
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
    pre_axis_extrema: bool = False,
) -> ComposedGlyph:
    """Pre-split for oblique axis extrema; optionally apply construct slant."""
    if pre_axis_extrema:
        glyph = ComposedGlyph(
            tuple(outline_with_axis_extrema_on_curve(s) for s in glyph.solids),
            tuple(outline_with_axis_extrema_on_curve(h) for h in glyph.holes),
            glyph.advance,
            glyph.context,
            anchors=glyph.anchors,
            design=glyph.design,
        )
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
