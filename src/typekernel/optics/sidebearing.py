"""Sidebearing / rhythm helpers.

Suggestions use the outline's width relative to ``x_height`` so wide and narrow
glyphs get different starting values. This is a *starting heuristic*, not a
substitute for spacing by eye or by gray-value models.
"""

from __future__ import annotations

from typekernel.geo.outline import Outline, bounds
from typekernel.optics.context import OpticalContext


def suggest_sidebearings(
    outline: Outline,
    ctx: OpticalContext,
) -> tuple[float, float]:
    """Suggest left and right sidebearings for ``outline``.

    Heuristic (Latin-leaning, documented — not universal):

    - Base = ``0.10 * x_height``
    - Scale by ``clamp(x_height / ink_width, 0.55, 1.45)`` so narrow glyphs get
      slightly more air and wide glyphs slightly less
    - Floor at ``0.04 * units_per_em``

    Returns ``(left, right)`` with equal values in v0. Callers should still
    refine by eye.
    """
    min_x, _, max_x, _ = bounds(outline)
    ink_width = max(max_x - min_x, 1.0)
    base = 0.10 * ctx.x_height
    scale = ctx.x_height / ink_width
    scale = max(0.55, min(1.45, scale))
    sb = max(0.04 * ctx.units_per_em, base * scale)
    return (sb, sb)
