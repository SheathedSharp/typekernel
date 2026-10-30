"""Optical whitespace measurement and spacing fit.

Sidebearings and kern here use **silhouette white space** along a vertical
band (typically baseline → x-height), not equal left/right heuristics and not
bounding-box gaps.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

from fontTools.misc.bezierTools import curveLineIntersections, lineLineIntersections

from typekernel.font.glyph import Glyph
from typekernel.font.kerning import KernPair, KernTable
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.context import OpticalContext

__all__ = [
    "OpticalSpacingResult",
    "fit_kern_pair",
    "ink_intervals_at_y",
    "measure_side_whitespace",
    "pair_gap_bbox",
    "pair_gap_optical",
    "silhouette_edge",
    "space_font",
    "space_word_optical",
    "suggest_sidebearings_optical",
    "suggest_sidebearings_tracy_bands",
    "with_sidebearings",
]

_T_EPS = 1e-6
DEFAULT_DEPTH = 0.12
_X_MERGE = 0.05


def _ink_outlines(glyph: Glyph) -> list[Outline]:
    return [glyph.outline] if glyph.outline.contours else []


def _segment_ray_xs(
    segment: LineSegment | CubicSegment,
    ray: list[tuple[float, float]],
) -> list[float]:
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
    depth: float | None = None,
) -> float:
    """Mean inset from the ink bbox edge to the silhouette along ``side``."""
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
        inset = (edge - min_x) if side == "left" else (max_x - edge)
        if depth is not None:
            inset = min(inset, depth)
        insets.append(inset)
    if not insets:
        return 0.0
    return sum(insets) / len(insets)


def suggest_sidebearings_optical(
    outline: Outline | list[Outline] | Glyph,
    ctx: OpticalContext,
    *,
    samples: int = 17,
    target_air: float | None = None,
) -> tuple[float, float]:
    """Suggest ``(lsb, rsb)`` from silhouette insets and a target air budget."""
    if isinstance(outline, Glyph):
        outlines: list[Outline] = _ink_outlines(outline)
    elif isinstance(outline, Outline):
        outlines = [outline]
    else:
        outlines = list(outline)
    y0 = 0.0
    y1 = float(ctx.x_height)
    depth = DEFAULT_DEPTH * y1
    left_inset = measure_side_whitespace(
        outlines, "left", y0=y0, y1=y1, samples=samples, depth=depth
    )
    right_inset = measure_side_whitespace(
        outlines, "right", y0=y0, y1=y1, samples=samples, depth=depth
    )
    ratio = float(getattr(ctx, "sidebearing_ratio", 0.2) or 0.2)
    air = float(target_air) if target_air is not None else ratio * y1
    floor = 0.0
    lsb = max(floor, air - left_inset)
    rsb = max(floor, air - right_inset)
    return (lsb, rsb)



def suggest_sidebearings_tracy_bands(
    outline: Outline | list[Outline] | Glyph,
    ctx: OpticalContext,
    *,
    samples_per_band: int = 7,
    target_air: float | None = None,
    band_weights: Sequence[tuple[float, float, float]] | None = None,
) -> tuple[float, float]:
    """Multi-band silhouette sidebearings (partial Tracy-style).

    Measures mean whitespace inset in horizontal bands between baseline and
    ``x_height`` (default thirds with mid-band weighted higher). This is **not**
    a gray-value / stem-band Tracy implementation — only silhouette scanlines
    already provided by :func:`measure_side_whitespace`.

    ``band_weights`` entries are ``(y0_frac, y1_frac, weight)`` of x-height.
    """
    if isinstance(outline, Glyph):
        outlines: list[Outline] = _ink_outlines(outline)
    elif isinstance(outline, Outline):
        outlines = [outline]
    else:
        outlines = list(outline)
    xh = float(ctx.x_height)
    depth = DEFAULT_DEPTH * xh
    weights = band_weights
    if weights is None:
        # Lower / mid / upper thirds; mid weighted like classic rhythm focus.
        weights = (
            (0.05, 0.35, 0.25),
            (0.35, 0.70, 0.50),
            (0.70, 0.95, 0.25),
        )
    left_acc = 0.0
    right_acc = 0.0
    w_sum = 0.0
    for y0f, y1f, w in weights:
        y0 = xh * float(y0f)
        y1 = xh * float(y1f)
        if y1 <= y0:
            continue
        li = measure_side_whitespace(
            outlines, "left", y0=y0, y1=y1, samples=samples_per_band, depth=depth
        )
        ri = measure_side_whitespace(
            outlines, "right", y0=y0, y1=y1, samples=samples_per_band, depth=depth
        )
        left_acc += li * float(w)
        right_acc += ri * float(w)
        w_sum += float(w)
    if w_sum <= 0:
        return suggest_sidebearings_optical(outlines, ctx, target_air=target_air)
    left_inset = left_acc / w_sum
    right_inset = right_acc / w_sum
    ratio = float(getattr(ctx, "sidebearing_ratio", 0.2) or 0.2)
    air = float(target_air) if target_air is not None else ratio * xh
    return (max(0.0, air - left_inset), max(0.0, air - right_inset))


def pair_gap_optical(
    left: Glyph,
    right: Glyph,
    *,
    kern: float = 0.0,
    samples: int = 17,
    y0: float | None = None,
    y1: float | None = None,
) -> float:
    """Mean optical gap between two glyphs' silhouettes (positive = open)."""
    left_o = _ink_outlines(left)
    right_o = _ink_outlines(right)
    if not left_o or not right_o:
        return float(left.advance) + kern
    try:
        _, lmin_y, _, lmax_y = union_bounds(left_o)
        _, rmin_y, _, rmax_y = union_bounds(right_o)
    except ValueError:
        return float(left.advance) + kern
    lo = y0 if y0 is not None else max(lmin_y, rmin_y)
    hi = y1 if y1 is not None else min(lmax_y, rmax_y)
    if hi <= lo:
        return float(left.advance) + kern
    gaps: list[float] = []
    for y in _y_samples(lo, hi, samples):
        l_edge = silhouette_edge(left_o, y, "right")
        r_edge = silhouette_edge(right_o, y, "left")
        if l_edge is None or r_edge is None:
            continue
        gaps.append((left.advance + kern + r_edge) - l_edge)
    if not gaps:
        return float(left.advance) + kern
    return sum(gaps) / len(gaps)


def pair_gap_bbox(left: Glyph, right: Glyph, *, kern: float = 0.0) -> float:
    """Bounding-box gap: ``left.advance - left.xmax + right.xmin + kern``."""
    try:
        lb = bounds(left.outline)
        rb = bounds(right.outline)
    except ValueError:
        return float(left.advance) + kern
    return (left.advance - lb[2]) + rb[0] + kern


def fit_kern_pair(
    left: Glyph,
    right: Glyph,
    target_gap: float,
    *,
    samples: int = 17,
) -> float:
    """Solve kern so optical gap ≈ ``target_gap``."""
    current = pair_gap_optical(left, right, kern=0.0, samples=samples)
    return float(target_gap - current)


def with_sidebearings(glyph: Glyph, lsb: float, rsb: float) -> Glyph:
    """Return a copy whose ink starts at ``lsb`` and advance is ``lsb+ink+rsb``."""
    if not glyph.outline.contours:
        return replace(glyph, advance=max(glyph.advance, lsb + rsb))
    box = bounds(glyph.outline)
    ink_w = float(box[2] - box[0])
    dx = lsb - float(box[0])
    from typekernel.draw.geomutil import map_segment
    from typekernel.geo.contour import Contour
    from typekernel.geo.point import Point

    def move(p: Point) -> Point:
        return Point(p.x + dx, p.y)

    shifted = Outline(
        tuple(
            Contour(tuple(map_segment(s, move) for s in c.segments), closed=c.closed)
            for c in glyph.outline.contours
        )
    )
    return replace(glyph, outline=shifted, advance=lsb + ink_w + rsb)


@dataclass(frozen=True, slots=True)
class OpticalSpacingResult:
    """Glyphs re-packed with optical sidebearings plus a fitted kern table."""

    glyphs: tuple[Glyph, ...]
    names: tuple[str, ...]
    kerning: KernTable
    target_gap: float


def space_word_optical(
    glyphs: Sequence[Glyph],
    names: Sequence[str],
    ctx: OpticalContext,
    *,
    samples: int = 17,
    target_gap: float | None = None,
) -> OpticalSpacingResult:
    """Re-space a word: optical sidebearings, then kern pairs to ``target_gap``."""
    if not glyphs:
        return OpticalSpacingResult((), (), KernTable(), 0.0)
    packed = [
        with_sidebearings(g, *suggest_sidebearings_optical(g, ctx, samples=samples))
        for g in glyphs
    ]
    if target_gap is None:
        gaps = [
            pair_gap_optical(packed[i], packed[i + 1], kern=0.0, samples=samples)
            for i in range(len(packed) - 1)
        ]
        gaps.sort()
        target = gaps[len(gaps) // 2] if gaps else 0.0
    else:
        target = target_gap
    pairs = [
        KernPair(
            names[i],
            names[i + 1],
            fit_kern_pair(packed[i], packed[i + 1], target, samples=samples),
        )
        for i in range(len(packed) - 1)
    ]
    return OpticalSpacingResult(
        glyphs=tuple(packed),
        names=tuple(names),
        kerning=KernTable(tuple(pairs)),
        target_gap=target,
    )


def space_font(
    glyphs: Mapping[str, Glyph],
    ctx: OpticalContext,
    *,
    samples: int = 17,
    target_air: float | None = None,
) -> dict[str, Glyph]:
    """Apply optical sidebearings across a glyph set."""
    out: dict[str, Glyph] = {}
    for name, g in glyphs.items():
        lsb, rsb = suggest_sidebearings_optical(
            g, ctx, samples=samples, target_air=target_air
        )
        out[name] = with_sidebearings(g, lsb, rsb)
    return out
