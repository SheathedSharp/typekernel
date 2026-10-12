"""Glyph metrics and simple word layout helpers.

An :class:`~typekernel.geo.outline.Outline` is pure geometry. Advances and
sidebearings are metrics bound later; this module helps authors compose words
without hand-tuning every x offset.
"""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.geo.outline import Outline, bounds


@dataclass(frozen=True, slots=True)
class GlyphMetrics:
    """Horizontal metrics for one outline (or composed glyph).

    Attributes:
        left_sidebearing: Distance from origin x=0 to the leftmost ink.
        right_sidebearing: Distance from rightmost ink to the advance width.
        advance: Full horizontal advance (LSB + ink width + RSB).
        ink_min_x: Leftmost x of the outline control bounds.
        ink_max_x: Rightmost x of the outline control bounds.
    """

    left_sidebearing: float
    right_sidebearing: float
    advance: float
    ink_min_x: float
    ink_max_x: float


def metrics_from_sidebearings(
    outline: Outline,
    left_sidebearing: float,
    right_sidebearing: float,
) -> GlyphMetrics:
    """Build metrics so ink sits after ``left_sidebearing`` from the origin.

    The outline itself is not translated; callers that draw at the glyph origin
    should offset by ``left_sidebearing - ink_min_x`` (see :func:`ink_origin_x`).
    """
    min_x, _, max_x, _ = bounds(outline)
    ink_width = max_x - min_x
    advance = left_sidebearing + ink_width + right_sidebearing
    return GlyphMetrics(
        left_sidebearing=left_sidebearing,
        right_sidebearing=right_sidebearing,
        advance=advance,
        ink_min_x=min_x,
        ink_max_x=max_x,
    )


def ink_origin_x(metrics: GlyphMetrics) -> float:
    """X translation that places ``ink_min_x`` at ``left_sidebearing``."""
    return metrics.left_sidebearing - metrics.ink_min_x


def layout_x_positions(
    advances: list[float],
    *,
    tracking: float = 0.0,
    origin_x: float = 0.0,
) -> list[float]:
    """Return the pen-x for each glyph given advances and uniform tracking.

    Tracking is added *between* glyphs (not after the last).
    """
    xs: list[float] = []
    x = origin_x
    for i, adv in enumerate(advances):
        xs.append(x)
        x += adv
        if i < len(advances) - 1:
            x += tracking
    return xs


def union_bounds(
    outlines: list[Outline],
) -> tuple[float, float, float, float]:
    """Axis-aligned control bounds of several outlines."""
    if not outlines:
        raise ValueError("union_bounds requires at least one outline")
    boxes = [bounds(o) for o in outlines]
    return (
        min(b[0] for b in boxes),
        min(b[1] for b in boxes),
        max(b[2] for b in boxes),
        max(b[3] for b in boxes),
    )
