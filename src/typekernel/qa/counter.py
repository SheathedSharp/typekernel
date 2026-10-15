"""Counter pinch measurement for R8 (weight-ladder QA)."""

from __future__ import annotations

from typekernel.geo.layout import union_bounds
from typekernel.optics.space import ink_intervals_at_y
from typekernel.parts.compose import ComposedGlyph

# B-16 bowl letters, round figures, and punctuation rings (not ``h``/``k`` stem slivers).
COUNTER_PINCH_CHARSET = frozenset(
    "0236789#%?@acemnos$CDEFOPQSTUZ"
)

__all__ = ["COUNTER_PINCH_CHARSET", "min_counter_gap"]


def min_counter_gap(glyph: ComposedGlyph, *, grid: int = 28) -> float:
    """Narrowest counter opening: hole width or solid–solid pinch in the body band."""
    best = float("inf")
    if glyph.holes:
        for hole in glyph.holes:
            x0, y0, x1, y1 = union_bounds([hole])
            best = min(best, x1 - x0, y1 - y0)
    if not glyph.solids:
        return best
    x0, y0, x1, y1 = union_bounds(list(glyph.solids))
    height = y1 - y0
    if height <= 0:
        return best
    y_lo = y0 + 0.22 * height
    y_hi = y0 + 0.78 * height
    solids = list(glyph.solids)
    for iy in range(grid):
        y = y_lo + (iy + 0.5) / grid * (y_hi - y_lo)
        runs = ink_intervals_at_y(solids, y)
        if len(runs) < 2:
            continue
        for j in range(len(runs) - 1):
            gap = runs[j + 1][0] - runs[j][1]
            if 0.0 < gap < best:
                best = gap
    return best
