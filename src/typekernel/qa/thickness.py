"""Geometric local stroke-thickness sampling for QA (not raster erosion)."""

from __future__ import annotations

from fontTools.pens.pointInsidePen import PointInsidePen

from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.pens import draw_outline
from typekernel.optics.stem import measure_oriented_stem
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.family import Controls

REFERENCE_THICKNESS_CHARS = "noHO"
THICKNESS_OUTLIER_FACTOR = 1.15
LINT_THICKNESS_GRID = 16
# Hook-root QA: minimum ``min_hook_thickness / thin`` on ``f t j g J``.
HOOK_MIN_THIN_RATIO = 0.26
HOOK_MIN_THIN_RATIO_SOFT = 0.22
HOOK_MIN_THIN_RATIO_DISPLAY = 0.19

__all__ = [
    "HOOK_MIN_THIN_RATIO",
    "HOOK_MIN_THIN_RATIO_DISPLAY",
    "HOOK_MIN_THIN_RATIO_SOFT",
    "LINT_THICKNESS_GRID",
    "REFERENCE_THICKNESS_CHARS",
    "THICKNESS_OUTLIER_FACTOR",
    "control_max_thickness_ratio",
    "hook_min_thin_floor",
    "max_local_thickness",
    "measurement_outline",
    "min_hook_thickness",
    "min_local_thickness",
    "thickness_ratio_to_stem",
]


def hook_min_thin_floor(ctx: DesignContext) -> float:
    """Minimum hook spring thickness for ``f t j g J`` (roundness-tiered)."""
    if ctx.roundness >= 0.5:
        ratio = HOOK_MIN_THIN_RATIO
    elif ctx.roundness >= 0.35:
        ratio = HOOK_MIN_THIN_RATIO_SOFT
    else:
        ratio = HOOK_MIN_THIN_RATIO_DISPLAY
    return ctx.thin * ratio


def control_max_thickness_ratio(controls: Controls) -> float:
    """Largest ``max_local_thickness / stem`` among control letters ``n/o/H/O``."""
    ctx = controls.context
    drawn = controls.build_all(REFERENCE_THICKNESS_CHARS)
    return max(
        thickness_ratio_to_stem(drawn[ch], ctx.stem, grid=LINT_THICKNESS_GRID)
        for ch in REFERENCE_THICKNESS_CHARS
    )


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


def min_local_thickness(
    glyph: ComposedGlyph,
    *,
    grid: int = 28,
    direction_step_deg: float = 15.0,
    y_min: float | None = None,
    y_max: float | None = None,
) -> float:
    """Smallest perpendicular span among grid samples inside an optional y band."""
    if not glyph.solids:
        return 0.0
    outline = measurement_outline(glyph)
    try:
        x0, y0, x1, y1 = union_bounds(list(glyph.solids))
    except ValueError:
        return 0.0
    if x1 <= x0 or y1 <= y0:
        return 0.0

    sample_y0 = y_min if y_min is not None else y0
    sample_y1 = y_max if y_max is not None else y1
    if sample_y1 <= sample_y0:
        return 0.0

    directions = tuple(
        float(d) for d in range(0, 180, max(1, round(direction_step_deg)))
    )
    best = float("inf")
    for iy in range(grid):
        fy = (iy + 0.5) / grid
        y = sample_y0 + fy * (sample_y1 - sample_y0)
        for ix in range(grid):
            fx = (ix + 0.5) / grid
            x = x0 + fx * (x1 - x0)
            if not _point_in_ink(x, y, glyph):
                continue
            local = _min_oriented_width(outline, (x, y), directions)
            if 0.0 < local < best:
                best = local
    return 0.0 if best == float("inf") else best


def min_hook_thickness(
    glyph: ComposedGlyph,
    char: str,
    ctx: DesignContext,
    *,
    grid: int = 28,
) -> float:
    """Min thickness in the hook/crossbar spring band (excludes terminal ball tips)."""
    from typekernel.parts.control import _hook_record, n_metrics

    m = n_metrics(ctx)
    xh = ctx.x_height
    hook_f = _hook_record(m, m.ascender, ctx)
    des = ctx.descender
    cap = ctx.cap_height
    bands: dict[str, tuple[float, float]] = {
        # Shoulder spring above the crossbar (skip bar-end slivers below mid x-height).
        "f": (0.50 * xh, hook_f.join_y),
        # Baseline hook: lower stem spring only (exclude full-width stem higher up).
        "t": (0.04 * xh, 0.42 * xh),
        # Descender hooks: spring band above the terminal ball (``j``: body solid only).
        "j": (des * 0.82, des * 0.62),
        "g": (des * 0.91, des * 0.36),
        # Cap ``J``: bowl spring (not descender; terminal is a vertical cut).
        "J": (cap * 0.32, cap * 0.46),
    }
    try:
        y_lo, y_hi = bands[char]
    except KeyError:
        raise ValueError(f"no hook thickness band for {char!r}") from None
    return min_local_thickness(glyph, grid=grid, y_min=y_lo, y_max=y_hi)


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


def thickness_ratio_to_stem(
    glyph: ComposedGlyph,
    stem: float,
    *,
    grid: int = 28,
) -> float:
    """``max_local_thickness / stem`` for a glyph built with that stem."""
    if stem <= 0:
        raise ValueError(f"stem must be positive, got {stem!r}")
    return max_local_thickness(glyph, grid=grid) / stem
