"""Geometric local stroke-thickness sampling for QA (not raster erosion)."""

from __future__ import annotations

from fontTools.pens.pointInsidePen import PointInsidePen

from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.pens import draw_outline
from typekernel.optics.stem import measure_oriented_stem
from typekernel.parts.caps import HMetrics
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import OMetrics, o_metrics
from typekernel.parts.family import FormSources

REFERENCE_THICKNESS_CHARS = "noHO"
THICKNESS_OUTLIER_FACTOR = 1.15
LINT_THICKNESS_GRID = 16
# Hook-root QA: minimum ``min_hook_thickness / thin`` on ``f t j g J``.
HOOK_MIN_THIN_RATIO = 0.26
HOOK_MIN_THIN_RATIO_SOFT = 0.22
HOOK_MIN_THIN_RATIO_DISPLAY = 0.19
# ``m`` crotch shelf (flat top between arches) horizontal ink ÷ stem (TK-102 / B-09).
M_CROTCH_SHELF_MIN_OVER_STEM = 0.28

__all__ = [
    "HOOK_MIN_THIN_RATIO",
    "HOOK_MIN_THIN_RATIO_DISPLAY",
    "HOOK_MIN_THIN_RATIO_SOFT",
    "LINT_THICKNESS_GRID",
    "M_CROTCH_SHELF_MIN_OVER_STEM",
    "REFERENCE_THICKNESS_CHARS",
    "THICKNESS_OUTLIER_FACTOR",
    "control_max_thickness_ratio",
    "figure_bar_over_stem_ink_ratio",
    "figure_nine_bar_over_stem_ink_ratio",
    "figure_stacked_ring_ink_ratio",
    "hook_min_thin_floor",
    "m_crotch_shelf_thickness_over_stem",
    "max_local_thickness",
    "measurement_outline",
    "min_hook_thickness",
    "min_local_thickness",
    "ometrics_ink_horizontal_over_vertical_ratio",
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


def m_crotch_shelf_thickness_over_stem(glyph: ComposedGlyph) -> float:
    """Horizontal ink across the ``m`` middle crotch shelf ÷ ``context.stem``.

    Probes the flat band between the first and second arch (B-09) so R9
    calibration can distinguish a solid black bridge from a healthy ``n``-like gap.
    """
    from typekernel.parts.control import NMetrics, _shoulder

    design = glyph.design
    if not isinstance(design, NMetrics):
        raise TypeError(f"expected NMetrics on ``m``, got {type(design)!r}")
    ctx = glyph.context
    s1 = _shoulder(design)
    s2 = _shoulder(design, s1.r0)
    xh = design.x_height
    x = (s1.r1 + s2.l0) / 2.0
    y = xh - ctx.stem * 0.035
    outline = measurement_outline(glyph)
    width = measure_oriented_stem(outline, (x, y), 0.0)
    if width is None or width <= 0.0:
        raise ValueError("m crotch shelf thickness probe missed ink")
    return width / ctx.stem


def control_max_thickness_ratio(controls: FormSources) -> float:
    """Largest ``max_local_thickness / stem`` among control letters ``n/o/H/O``."""
    ctx = controls.context
    drawn = controls.derive(REFERENCE_THICKNESS_CHARS)
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


def ometrics_ink_horizontal_over_vertical_ratio(
    glyph: ComposedGlyph,
    *,
    side_y_fraction: float = 0.5,
    side_x_fraction: float | None = None,
) -> float:
    """Horizontal ring stroke ÷ vertical side stroke on ``OMetrics`` probe stations."""
    design = glyph.design
    if not isinstance(design, OMetrics):
        raise TypeError(f"expected OMetrics design, got {type(design)!r}")
    m = design
    outline = measurement_outline(glyph)
    cx = m.rx
    cy_side = m.x_height * side_y_fraction
    top_y = m.x_height + m.overshoot * 0.5
    side_x = (
        m.width * side_x_fraction
        if side_x_fraction is not None
        else m.width - m.thickness_v * 0.5
    )
    top_w = measure_oriented_stem(outline, (cx, top_y - m.thickness_h * 0.5), 0.0)
    side_w = measure_oriented_stem(outline, (side_x, cy_side), 90.0)
    if top_w is None or side_w is None or side_w <= 0.0:
        raise ValueError("contrast ink probes missed ink on OMetrics glyph")
    return top_w / side_w


def figure_bar_over_stem_ink_ratio(
    glyph: ComposedGlyph,
    *,
    stem_y_fraction: float = 0.75,
) -> float:
    """Top bar thickness ÷ vertical stem thickness (``5``-style figures)."""
    design = glyph.design
    if not isinstance(design, HMetrics):
        raise TypeError(f"expected HMetrics design, got {type(design)!r}")
    h = design
    outline = measurement_outline(glyph)
    top_w = measure_oriented_stem(
        outline, (h.width * 0.5, h.cap_height - h.bar * 0.5), 0.0
    )
    side_w = measure_oriented_stem(
        outline, (h.stem * 0.5, h.cap_height * stem_y_fraction), 90.0
    )
    if top_w is None or side_w is None or side_w <= 0.0:
        raise ValueError("bar/stem ink probes missed ink on figure glyph")
    return top_w / side_w


def figure_stacked_ring_ink_ratio(glyph: ComposedGlyph, *, waist: float) -> float:
    """Lower-bowl ring horizontal ÷ vertical thickness (``8`` waist band)."""
    design = glyph.design
    if not isinstance(design, HMetrics):
        raise TypeError(f"expected HMetrics design, got {type(design)!r}")
    h = design
    o = o_metrics(glyph.context)
    cap, os_ = h.cap_height, o.overshoot
    bar, w = h.bar, h.width
    tv = min(bar, 0.25 * cap)
    ym = waist * cap
    cx = w / 2.0
    ry_l = (ym + tv / 2.0 + os_) / 2.0
    cy_l = ry_l - os_
    tv_ring = min(tv, 0.6 * ry_l)
    outline = measurement_outline(glyph)
    side_x = w * 0.85
    cy_side = waist * cap * 0.45
    side_w = measure_oriented_stem(outline, (side_x, cy_side), 90.0)
    top_y = cy_l + ry_l - tv_ring * 0.5
    top_w = measure_oriented_stem(outline, (cx, top_y), 0.0)
    if top_w is None or side_w is None or side_w <= 0.0:
        raise ValueError("stacked-ring ink probes missed ink on figure glyph")
    return top_w / side_w


def figure_nine_bar_over_stem_ink_ratio(glyph: ComposedGlyph) -> float:
    """``9`` bowl crossbar thickness ÷ stem thickness (rotated ``6`` topology)."""
    design = glyph.design
    if not isinstance(design, HMetrics):
        raise TypeError(f"expected HMetrics design, got {type(design)!r}")
    h = design
    outline = measurement_outline(glyph)
    top_w = measure_oriented_stem(
        outline, (h.width * 0.5, h.cap_height - h.bar * 0.5), 0.0
    )
    side_w = measure_oriented_stem(
        outline, (h.width * 0.85, h.cap_height * 0.65), 90.0
    )
    if top_w is None or side_w is None or side_w <= 0.0:
        raise ValueError("nine ink probes missed ink on figure glyph")
    return top_w / side_w


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
    from typekernel.parts.control import _crossbar, _hook_record, n_metrics

    m = n_metrics(ctx)
    xh = ctx.x_height
    hook_f = _hook_record(m, m.ascender, ctx)
    bar_top = _crossbar(ctx, m, hook_f, xh)[1]
    des = ctx.descender
    cap = ctx.cap_height
    bands: dict[str, tuple[float, float]] = {
        # Shoulder spring above the boolean crossbar (skip stem/bar seam corners).
        "f": (bar_top + 0.06 * m.stem, hook_f.join_y),
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
