"""Optical whitespace measurement and spacing fit.

Sidebearings and kern here use **silhouette white space** along a vertical
band (typically baseline → x-height), not equal left/right heuristics and not
bounding-box gaps. Bounding-box gaps can look even while the word still feels
uneven — that is exactly what this module measures.
"""

from __future__ import annotations

from dataclasses import dataclass

from fontTools.misc.bezierTools import curveLineIntersections, lineLineIntersections

from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.context import OpticalContext
from typekernel.parts.compose import ComposedGlyph, translate_outline
from typekernel.parts.context import DesignContext
from typekernel.parts.metrics import KernPair, KernTable

_T_EPS = 1e-6
_X_MERGE = 0.05


def _ink_outlines(glyph: ComposedGlyph) -> list[Outline]:
    return list(glyph.solids) + list(glyph.holes)


def _segment_ray_xs(
    segment: LineSegment | CubicSegment,
    ray: list[tuple[float, float]],
) -> list[float]:
    """Return intersection x values with ``t1,t2`` clamped to the segment."""
    if isinstance(segment, LineSegment):
        hits = lineLineIntersections(
            segment.p0.as_tuple(),
            segment.p1.as_tuple(),
            ray[0],
            ray[1],
        )
    else:
        hits = curveLineIntersections([p.as_tuple() for p in segment.points], ray)
    out: list[float] = []
    for hit in hits:
        t1 = float(hit.t1)
        t2 = float(hit.t2)
        if -_T_EPS <= t1 <= 1.0 + _T_EPS and -_T_EPS <= t2 <= 1.0 + _T_EPS:
            out.append(float(hit.pt[0]))
    return out


def _merge_xs(xs: list[float], tol: float = _X_MERGE) -> list[float]:
    if not xs:
        return []
    xs = sorted(xs)
    merged = [xs[0]]
    for x in xs[1:]:
        if x - merged[-1] > tol:
            merged.append(x)
    return merged


def ink_intervals_at_y(outlines: list[Outline], y: float) -> list[tuple[float, float]]:
    """Even-odd filled x-intervals of ``outlines`` on the horizontal line at ``y``."""
    if not outlines:
        return []
    min_x = float("inf")
    max_x = float("-inf")
    for outline in outlines:
        try:
            a, _, c, _ = bounds(outline)
        except ValueError:
            continue
        min_x = min(min_x, a)
        max_x = max(max_x, c)
    if not (min_x < max_x):
        return []
    margin = max(1.0, (max_x - min_x) * 0.05 + 1.0)
    ray = [(min_x - margin, y), (max_x + margin, y)]
    xs: list[float] = []
    for outline in outlines:
        for segment in outline.iter_segments():
            xs.extend(_segment_ray_xs(segment, ray))
    unique = _merge_xs(xs)
    if len(unique) < 2:
        return []
    return [(unique[i], unique[i + 1]) for i in range(0, len(unique) - 1, 2)]


def silhouette_edge(outlines: list[Outline], y: float, side: str) -> float | None:
    """Leftmost or rightmost ink x at ``y``, or ``None`` if the scanline misses."""
    intervals = ink_intervals_at_y(outlines, y)
    if not intervals:
        return None
    if side == "left":
        return min(a for a, _ in intervals)
    if side == "right":
        return max(b for _, b in intervals)
    raise ValueError("side must be 'left' or 'right'")


def _y_samples(y0: float, y1: float, count: int) -> list[float]:
    if count < 2:
        return [(y0 + y1) / 2.0]
    return [y0 + (y1 - y0) * i / (count - 1) for i in range(count)]


def measure_side_whitespace(
    outline: Outline | list[Outline],
    side: str,
    *,
    y0: float,
    y1: float,
    samples: int = 17,
) -> float:
    """Mean inset from the ink bbox edge to the silhouette along ``side``.

    Large inset (diagonal flanks, open bowls) means more corner white — optical
    sidebearings should usually be smaller on that side.
    """
    outlines = [outline] if isinstance(outline, Outline) else list(outline)
    try:
        min_x, _, max_x, _ = union_bounds(outlines)
    except ValueError:
        return 0.0
    insets: list[float] = []
    for y in _y_samples(y0, y1, samples):
        edge = silhouette_edge(outlines, y, side)
        if edge is None:
            continue
        if side == "left":
            insets.append(edge - min_x)
        else:
            insets.append(max_x - edge)
    if not insets:
        return 0.0
    return sum(insets) / len(insets)


def suggest_sidebearings_optical(
    outline: Outline | list[Outline] | ComposedGlyph,
    ctx: DesignContext | OpticalContext,
    *,
    samples: int = 17,
    target_air: float | None = None,
) -> tuple[float, float]:
    """Suggest ``(lsb, rsb)`` from silhouette insets and a target air budget.

    ``lsb = target_air - mean_left_inset`` (floored), likewise for ``rsb``.
    Flat stems (inset ≈ 0) keep nearly full ``target_air``; open / diagonal
    flanks pull the bearing in so neighboring letters do not look sparse.
    """
    if isinstance(outline, ComposedGlyph):
        outlines = _ink_outlines(outline)
    else:
        outlines = [outline] if isinstance(outline, Outline) else list(outline)

    if isinstance(ctx, DesignContext):
        x_height = ctx.x_height
        units = ctx.units_per_em
        ratio = ctx.sidebearing_ratio
    else:
        x_height = ctx.x_height
        units = ctx.units_per_em
        ratio = 0.10

    y0 = 0.0
    y1 = x_height
    air = (
        max(0.04 * units, ratio * x_height)
        if target_air is None
        else target_air
    )
    left_inset = measure_side_whitespace(outlines, "left", y0=y0, y1=y1, samples=samples)
    right_inset = measure_side_whitespace(outlines, "right", y0=y0, y1=y1, samples=samples)
    floor = 0.02 * units
    lsb = max(floor, air - left_inset)
    rsb = max(floor, air - right_inset)
    return (lsb, rsb)


def pair_gap_optical(
    left: ComposedGlyph,
    right: ComposedGlyph,
    *,
    kern: float = 0.0,
    samples: int = 17,
    y0: float | None = None,
    y1: float | None = None,
) -> float:
    """Mean silhouette gap between ``left`` and ``right`` (design units).

    Positive = separation; negative = silhouette overlap in the band. Uses the
    left glyph's advance + ``kern`` as the pen advance (tracking not included).
    """
    ctx = left.context
    band0 = 0.0 if y0 is None else y0
    band1 = ctx.x_height if y1 is None else y1
    left_o = _ink_outlines(left)
    right_o = _ink_outlines(right)
    gaps: list[float] = []
    for y in _y_samples(band0, band1, samples):
        l_edge = silhouette_edge(left_o, y, "right")
        r_edge = silhouette_edge(right_o, y, "left")
        if l_edge is None or r_edge is None:
            continue
        # right glyph origin at left.advance + kern
        gaps.append((left.advance + kern + r_edge) - l_edge)
    if not gaps:
        # Fall back to bbox gap so callers always get a number.
        lb = union_bounds(left_o)
        rb = union_bounds(right_o)
        return (left.advance - lb[2]) + rb[0] + kern
    return sum(gaps) / len(gaps)


def pair_gap_bbox(
    left: ComposedGlyph,
    right: ComposedGlyph,
    *,
    kern: float = 0.0,
) -> float:
    """Bounding-box gap: ``RSB(left) + LSB(right) + kern``."""
    lb = union_bounds(_ink_outlines(left))
    rb = union_bounds(_ink_outlines(right))
    return (left.advance - lb[2]) + rb[0] + kern


def fit_kern_pair(
    left: ComposedGlyph,
    right: ComposedGlyph,
    target_gap: float,
    *,
    samples: int = 17,
    lo: float = -200.0,
    hi: float = 80.0,
    iterations: int = 24,
) -> float:
    """Binary-search kern so :func:`pair_gap_optical` ≈ ``target_gap``."""
    best = 0.0
    best_err = float("inf")
    low, high = lo, hi
    for _ in range(iterations):
        mid = (low + high) / 2.0
        gap = pair_gap_optical(left, right, kern=mid, samples=samples)
        err = abs(gap - target_gap)
        if err < best_err:
            best_err = err
            best = mid
        if gap > target_gap:
            # too much air → pull together (more negative / less positive kern)
            high = mid
        else:
            low = mid
    return best


def with_sidebearings(glyph: ComposedGlyph, lsb: float, rsb: float) -> ComposedGlyph:
    """Return a copy whose ink starts at ``lsb`` and advance is ``lsb+ink+rsb``."""
    ink = _ink_outlines(glyph)
    box = union_bounds(ink)
    ink_w = box[2] - box[0]
    dx = lsb - box[0]
    solids = tuple(translate_outline(o, dx) for o in glyph.solids)
    holes = tuple(translate_outline(h, dx) for h in glyph.holes)
    return ComposedGlyph(solids, holes, lsb + ink_w + rsb, glyph.context)


@dataclass(frozen=True, slots=True)
class OpticalSpacingResult:
    """Glyphs re-packed with optical sidebearings plus a fitted kern table."""

    glyphs: tuple[ComposedGlyph, ...]
    names: tuple[str, ...]
    kerning: KernTable
    target_gap: float


def space_word_optical(
    glyphs: list[ComposedGlyph],
    names: list[str],
    *,
    target_gap: float | None = None,
    samples: int = 17,
) -> OpticalSpacingResult:
    """Re-space a word: optical sidebearings, then kern pairs to ``target_gap``.

    If ``target_gap`` is omitted, uses the median *bbox* gap of the input word
    (with zero kern) so overall tightness stays familiar while optical rhythm
    evening happens in the pair fits.
    """
    if len(glyphs) != len(names):
        raise ValueError("names length must match glyphs")
    if not glyphs:
        return OpticalSpacingResult((), (), KernTable(), 0.0)

    ctx = glyphs[0].context
    # 1) optical sidebearings per glyph
    packed: list[ComposedGlyph] = []
    for g in glyphs:
        lsb, rsb = suggest_sidebearings_optical(g, ctx, samples=samples)
        packed.append(with_sidebearings(g, lsb, rsb))

    # 2) choose target from median *optical* gap (kern=0) so overall air stays
    # familiar while pair rhythm evens out. Bbox median tends to crush pairs
    # that already carry large silhouette white (diagonals, hooks).
    if target_gap is None:
        opt_gaps = [
            pair_gap_optical(packed[i], packed[i + 1], kern=0.0, samples=samples)
            for i in range(len(packed) - 1)
        ]
        opt_gaps.sort()
        target = opt_gaps[len(opt_gaps) // 2] if opt_gaps else 0.16 * ctx.x_height
    else:
        target = target_gap

    # 3) fit each pair
    pairs: list[KernPair] = []
    for i in range(len(packed) - 1):
        k = fit_kern_pair(packed[i], packed[i + 1], target, samples=samples)
        pairs.append(KernPair(names[i], names[i + 1], k))

    return OpticalSpacingResult(
        glyphs=tuple(packed),
        names=tuple(names),
        kerning=KernTable(tuple(pairs)),
        target_gap=target,
    )
