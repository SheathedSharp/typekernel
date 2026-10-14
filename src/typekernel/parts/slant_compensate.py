"""Construct-slant draw-time compensation (TK-402)."""

from __future__ import annotations

import math

from typekernel.parts.context import DesignContext

__all__ = ["horizontal_slant_compensation"]


def horizontal_slant_compensation(ctx: DesignContext) -> float:
    """Scale horizontal stroke thickness before :func:`~typekernel.parts.italic.slant_composed_glyph`."""
    slant = abs(ctx.italic_slant_deg)
    if slant < 1e-9:
        return 1.0
    return 1.0 / math.cos(math.radians(slant))
