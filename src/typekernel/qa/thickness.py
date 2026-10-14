"""Geometric local stroke-thickness sampling for QA (not raster erosion)."""

from __future__ import annotations

from fontTools.pens.pointInsidePen import PointInsidePen

from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.pens import draw_outline
from typekernel.optics.stem import measure_oriented_stem
from typekernel.parts.compose import ComposedGlyph

__all__ = [
    "max_local_thickness",
    "measurement_outline",
    "thickness_ratio_to_stem",
]


def measurement_outline(glyph: ComposedGlyph) -> Outline:
    """All solid and counter contours in one outline for ray probes."""
    contours = tuple(
        contour
        for part in (*glyph.solids, *glyph.holes)
        for contour in part.contours
    )
    return Outline(contours)


def _point_in_ink(x: float, y: float, glyph: ComposedGlyph) -> bool:
    def _inside(outline: Outline) -> bool:
        pen = PointInsidePen(None, (x, y))
        draw_outline(outline, pen)
        return bool(pen.getResult())

    if not any(_inside(solid) for solid in glyph.solids):
        return False
    return not any(_inside(hole) for hole in glyph.holes)


def max_local_thickness(
    glyph: ComposedGlyph,
    *,
    grid: int = 28,
    direction_step_deg: float = 15.0,
) -> float:
    """Largest perpendicular span found by grid sampling and oriented stem probes.

    Uses :func:`~typekernel.optics.stem.measure_oriented_stem` (even-odd ray
    crossings), not square morphological erosion, so ``o`` rings stay near
    ``1.05–1.08×`` stem rather than inflating toward ``√2×``.
    """
    if not glyph.solids:
        return 0.0
    outline = measurement_outline(glyph)
    try:
        x0, y0, x1, y1 = union_bounds(list(glyph.solids))
    except ValueError:
        return 0.0
    if x1 <= x0 or y1 <= y0:
        return 0.0

    directions = tuple(
        float(d) for d in range(0, 180, max(1, round(direction_step_deg)))
    )
    best = 0.0
    for iy in range(grid):
        fy = (iy + 0.5) / grid
        y = y0 + fy * (y1 - y0)
        for ix in range(grid):
            fx = (ix + 0.5) / grid
            x = x0 + fx * (x1 - x0)
            if not _point_in_ink(x, y, glyph):
                continue
            local = _min_oriented_width(outline, (x, y), directions)
            best = max(best, local)
    return best


def _min_oriented_width(
    outline: Outline,
    origin: tuple[float, float],
    directions: tuple[float, ...],
) -> float:
    """Narrowest even-odd span at ``origin`` across stroke bearings."""
    widths = [
        w
        for direction in directions
        for w in (measure_oriented_stem(outline, origin, direction),)
        if w is not None and w > 0.0
    ]
    return min(widths) if widths else 0.0


def thickness_ratio_to_stem(glyph: ComposedGlyph, stem: float) -> float:
    """``max_local_thickness / stem`` for a glyph built with that stem."""
    if stem <= 0:
        raise ValueError(f"stem must be positive, got {stem!r}")
    return max_local_thickness(glyph) / stem
