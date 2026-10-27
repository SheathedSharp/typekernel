"""Stem measurement, diagonal compensation, and designed-delta equalization.

Vertical and oriented stem widths are measured from designed outline
intersections (ray spans), never taken from a stroke-width constant as a
weight axis. Equalization redistributes **x** (or **y**) of on-curve / handle
points inside each stem band so measured widths hit a target — it is not
``buffer`` / pen-radius weight.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from fontTools.misc.bezierTools import curveLineIntersections, lineLineIntersections

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline, bounds
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.context import OpticalContext

_T_EPS = 1e-6

SidePolicy = Literal["both", "left", "right"]


@dataclass(frozen=True, slots=True)
class VerticalStemSpan:
    """One filled vertical stem span along a horizontal probe."""

    left: float
    right: float
    y: float

    @property
    def width(self) -> float:
        return self.right - self.left

    @property
    def center_x(self) -> float:
        return (self.left + self.right) / 2.0


@dataclass(frozen=True, slots=True)
class HorizontalStemSpan:
    """One filled horizontal bar span along a vertical probe."""

    bottom: float
    top: float
    x: float

    @property
    def width(self) -> float:
        """Thickness of the bar (vertical extent)."""
        return self.top - self.bottom

    @property
    def center_y(self) -> float:
        return (self.bottom + self.top) / 2.0


@dataclass(frozen=True, slots=True)
class StemContrastReport:
    """Measured vertical vs horizontal stem widths on an outline."""

    vertical: tuple[float, ...]
    horizontal: tuple[float, ...]
    vertical_median: float | None
    horizontal_median: float | None

    @property
    def contrast_ratio(self) -> float | None:
        """``horizontal_median / vertical_median`` when both exist."""
        if (
            self.vertical_median is None
            or self.horizontal_median is None
            or self.vertical_median <= 0
        ):
            return None
        return self.horizontal_median / self.vertical_median


def measure_vertical_stem(outline: Outline, x: float) -> float | None:
    """Measure the width of the vertical stem nearest to ``x``.

    Casts a **horizontal** probe ray through the vertical mid-point of the
    outline's control-point bounds. Intersection ``x`` values with every
    segment are collected and sorted. Under a simple even-odd crossing model,
    consecutive pairs ``(xs[0], xs[1])``, ``(xs[2], xs[3])``, … are treated as
    filled stem spans. The span that contains ``x`` is returned as its width;
    if none contains ``x``, returns ``None``.
    """
    spans = list_vertical_stems(outline)
    for span in spans:
        if span.left <= x <= span.right:
            return span.width if span.width > 0.0 else None
    return None


def measure_horizontal_stem(outline: Outline, y: float) -> float | None:
    """Measure the thickness of the horizontal bar containing ``y``.

    Casts a **vertical** probe through the horizontal mid-point of the bounds.
    """
    spans = list_horizontal_stems(outline)
    for span in spans:
        if span.bottom <= y <= span.top:
            return span.width if span.width > 0.0 else None
    return None


def list_vertical_stems(
    outline: Outline,
    *,
    y: float | None = None,
    min_width: float = 1.0,
    max_width: float | None = None,
) -> list[VerticalStemSpan]:
    """Even-odd filled spans on a horizontal probe (candidate vertical stems)."""
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return []
    y_probe = (min_y + max_y) / 2.0 if y is None else y
    margin = max(1.0, (max_x - min_x) * 0.05 + 1.0)
    ray = [(min_x - margin, y_probe), (max_x + margin, y_probe)]
    xs: list[float] = []
    for segment in outline.iter_segments():
        xs.extend(_intersection_xs(segment, ray))
    unique = _merge_sorted(xs)
    spans: list[VerticalStemSpan] = []
    for i in range(0, len(unique) - 1, 2):
        left, right = unique[i], unique[i + 1]
        w = right - left
        if w < min_width:
            continue
        if max_width is not None and w > max_width:
            continue
        spans.append(VerticalStemSpan(left=left, right=right, y=y_probe))
    return spans


def list_horizontal_stems(
    outline: Outline,
    *,
    x: float | None = None,
    min_width: float = 1.0,
    max_width: float | None = None,
) -> list[HorizontalStemSpan]:
    """Even-odd filled spans on a vertical probe (candidate horizontal bars)."""
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return []
    x_probe = (min_x + max_x) / 2.0 if x is None else x
    margin = max(1.0, (max_y - min_y) * 0.05 + 1.0)
    ray = [(x_probe, min_y - margin), (x_probe, max_y + margin)]
    ys: list[float] = []
    for segment in outline.iter_segments():
        for _hx, hy in _intersection_points(segment, ray):
            ys.append(hy)
    unique = _merge_sorted(ys)
    spans: list[HorizontalStemSpan] = []
    for i in range(0, len(unique) - 1, 2):
        bottom, top = unique[i], unique[i + 1]
        w = top - bottom
        if w < min_width:
            continue
        if max_width is not None and w > max_width:
            continue
        spans.append(HorizontalStemSpan(bottom=bottom, top=top, x=x_probe))
    return spans


def measure_oriented_stem(
    outline: Outline,
    origin: tuple[float, float],
    direction_deg: float,
) -> float | None:
    """Perpendicular stem width at ``origin`` along stroke ``direction_deg``.

    ``direction_deg`` is the centerline bearing (0° = +x, 90° = +y). A probe
    ray through ``origin`` runs along the *normal* (direction + 90°). Even-odd
    spans along that ray give the local thickness; the span containing
    ``origin`` is returned.
    """
    ox, oy = origin
    theta = math.radians(direction_deg + 90.0)
    nx, ny = math.cos(theta), math.sin(theta)
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return None
    diag = math.hypot(max_x - min_x, max_y - min_y) + 10.0
    ray = [
        (ox - nx * diag, oy - ny * diag),
        (ox + nx * diag, oy + ny * diag),
    ]
    ts: list[float] = []
    for segment in outline.iter_segments():
        for hit_x, hit_y in _intersection_points(segment, ray):
            ts.append((hit_x - ox) * nx + (hit_y - oy) * ny)
    if len(ts) < 2:
        return None
    unique = _merge_sorted(ts)
    for i in range(0, len(unique) - 1, 2):
        a, b = unique[i], unique[i + 1]
        if a <= 0.0 <= b:
            width = b - a
            return width if width > 0.0 else None
    return None


def diagonal_compensation(
    angle_from_vertical_deg: float,
    stem: float,
    *,
    contrast: float = 1.0,
    floor: float = 0.55,
) -> float:
    """Perpendicular thickness so a diagonal matches a vertical stem optically.

    ``angle_from_vertical_deg`` is 0 for a vertical bar and 90 for a horizontal
    bar. A constant geometric thickness reads heavier on the diagonal; thinning
    by ``max(floor, |cos φ|)`` keeps apparent weight closer to the upright
    stem. ``contrast`` further leans the result toward the family's thin target
    as the bar approaches horizontal (``w *= 1 - (1-contrast)*|sin φ|``).

    This is a construction aid for :func:`~starter diagonal strokes`,
    not a weight-axis buffer / stroke expand.
    """
    if stem <= 0:
        raise ValueError(f"stem must be positive, got {stem!r}")
    if contrast <= 0:
        raise ValueError(f"contrast must be positive, got {contrast!r}")
    if floor <= 0 or floor > 1.0:
        raise ValueError(f"floor must be in (0, 1], got {floor!r}")
    phi = math.radians(angle_from_vertical_deg)
    w = stem * max(floor, abs(math.cos(phi)))
    w *= 1.0 - (1.0 - contrast) * abs(math.sin(phi))
    return w


def vertical_equiv_from_diagonal(
    measured_perp: float,
    angle_from_vertical_deg: float = 45.0,
    *,
    contrast: float = 1.0,
    floor: float = 0.55,
) -> float:
    """Invert :func:`diagonal_compensation` to recover an upright stem equivalent.

    Shared by construction optics and style QA when an oriented (diagonal)
    thickness must be compared to a vertical control stem.
    """
    if measured_perp <= 0:
        raise ValueError(f"measured_perp must be positive, got {measured_perp!r}")
    if contrast <= 0:
        raise ValueError(f"contrast must be positive, got {contrast!r}")
    if floor <= 0 or floor > 1.0:
        raise ValueError(f"floor must be in (0, 1], got {floor!r}")
    phi = math.radians(angle_from_vertical_deg)
    factor = max(floor, abs(math.cos(phi)))
    factor *= 1.0 - (1.0 - contrast) * abs(math.sin(phi))
    if factor <= 0:
        raise ValueError("compensation factor collapsed to non-positive")
    return measured_perp / factor


def horizontal_vs_vertical_report(
    outline: Outline,
    *,
    y: float | None = None,
    x: float | None = None,
) -> StemContrastReport:
    """Measure all vertical and horizontal stem spans for contrast diagnostics."""
    v_spans = list_vertical_stems(outline, y=y)
    h_spans = list_horizontal_stems(outline, x=x)
    v_w = tuple(s.width for s in v_spans)
    h_w = tuple(s.width for s in h_spans)
    return StemContrastReport(
        vertical=v_w,
        horizontal=h_w,
        vertical_median=_median(v_w),
        horizontal_median=_median(h_w),
    )


def equalize_vertical_stems(
    outline: Outline,
    target_width: float,
    ctx: OpticalContext | None = None,
    *,
    y: float | None = None,
    side: SidePolicy = "both",
    min_width: float = 1.0,
    max_width: float | None = None,
    band_pad: float = 0.5,
) -> Outline:
    """Equalize vertical stem widths toward ``target_width`` by designed deltas.

    Each stem band found by :func:`list_vertical_stems` has its points'
    **x** coordinates remapped so the band width becomes ``target_width``.
    Remapping is a designed point displacement — never stroke expand.

    ``side``:
      - ``both`` (default): grow/shrink symmetrically about the stem center
      - ``left``: keep the right edge fixed; move the left edge
      - ``right``: keep the left edge fixed; move the right edge

    ``ctx`` is accepted for API compatibility (alignment metadata); unused for
    the geometric remap itself.
    """
    del ctx  # reserved for future zone-aware selection
    if target_width <= 0:
        raise ValueError(f"target_width must be positive, got {target_width!r}")
    if side not in ("both", "left", "right"):
        raise ValueError(f"unknown side policy: {side!r}")

    spans = list_vertical_stems(
        outline, y=y, min_width=min_width, max_width=max_width
    )
    if not spans:
        return outline

    # (select_lo, select_hi, old_left, old_right, new_left, new_right)
    remaps: list[tuple[float, float, float, float, float, float]] = []
    for span in spans:
        if abs(span.width - target_width) < 1e-9:
            continue
        if side == "both":
            half = (target_width - span.width) / 2.0
            new_left = span.left - half
            new_right = span.right + half
        elif side == "left":
            new_left = span.right - target_width
            new_right = span.right
        else:  # right
            new_left = span.left
            new_right = span.left + target_width
        remaps.append(
            (
                span.left - band_pad,
                span.right + band_pad,
                span.left,
                span.right,
                new_left,
                new_right,
            )
        )

    if not remaps:
        return outline

    def map_pt(p: Point) -> Point:
        x = p.x
        for sel_lo, sel_hi, old_l, old_r, new_l, new_r in remaps:
            if sel_lo <= x <= sel_hi:
                old_w = old_r - old_l
                if old_w < 1e-12:
                    x = (new_l + new_r) / 2.0
                else:
                    x = new_l + (x - old_l) / old_w * (new_r - new_l)
                break
        return Point(x, p.y)

    return _map_outline_points(outline, map_pt)


def equalize_horizontal_stems(
    outline: Outline,
    target_thickness: float,
    ctx: OpticalContext | None = None,
    *,
    x: float | None = None,
    side: Literal["both", "bottom", "top"] = "both",
    min_width: float = 1.0,
    max_width: float | None = None,
    band_pad: float = 0.5,
) -> Outline:
    """Equalize horizontal bar thickness by designed **y** deltas (not expand)."""
    del ctx
    if target_thickness <= 0:
        raise ValueError(f"target_thickness must be positive, got {target_thickness!r}")
    if side not in ("both", "bottom", "top"):
        raise ValueError(f"unknown side policy: {side!r}")

    spans = list_horizontal_stems(
        outline, x=x, min_width=min_width, max_width=max_width
    )
    if not spans:
        return outline

    remaps: list[tuple[float, float, float, float, float, float]] = []
    for span in spans:
        if abs(span.width - target_thickness) < 1e-9:
            continue
        if side == "both":
            half = (target_thickness - span.width) / 2.0
            new_b = span.bottom - half
            new_t = span.top + half
        elif side == "bottom":
            new_b = span.top - target_thickness
            new_t = span.top
        else:
            new_b = span.bottom
            new_t = span.bottom + target_thickness
        remaps.append(
            (
                span.bottom - band_pad,
                span.top + band_pad,
                span.bottom,
                span.top,
                new_b,
                new_t,
            )
        )

    if not remaps:
        return outline

    def map_pt(p: Point) -> Point:
        y = p.y
        for sel_lo, sel_hi, old_b, old_t, new_b, new_t in remaps:
            if sel_lo <= y <= sel_hi:
                old_w = old_t - old_b
                if old_w < 1e-12:
                    y = (new_b + new_t) / 2.0
                else:
                    y = new_b + (y - old_b) / old_w * (new_t - new_b)
                break
        return Point(p.x, y)

    return _map_outline_points(outline, map_pt)


def _median(values: tuple[float, ...] | list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    mid = len(s) // 2
    if len(s) % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def _map_outline_points(
    outline: Outline, mapper: Callable[[Point], Point]
) -> Outline:
    contours: list[Contour] = []
    for c in outline.contours:
        segs: list[LineSegment | CubicSegment] = []
        for seg in c.segments:
            pts = [mapper(p) for p in seg.points]
            if isinstance(seg, LineSegment):
                segs.append(LineSegment(pts[0], pts[1]))
            else:
                segs.append(CubicSegment(pts[0], pts[1], pts[2], pts[3]))
        contours.append(Contour(tuple(segs), closed=c.closed))
    return Outline(tuple(contours))


def _merge_sorted(values: list[float], tol: float = 0.05) -> list[float]:
    if not values:
        return []
    values = sorted(values)
    out = [values[0]]
    for v in values[1:]:
        if v - out[-1] > tol:
            out.append(v)
    return out


def _intersection_xs(
    segment: LineSegment | CubicSegment,
    ray: list[tuple[float, float]],
) -> list[float]:
    return [pt[0] for pt in _intersection_points(segment, ray)]


def _intersection_points(
    segment: LineSegment | CubicSegment,
    ray: list[tuple[float, float]],
) -> list[tuple[float, float]]:
    if isinstance(segment, LineSegment):
        hits = lineLineIntersections(
            segment.p0.as_tuple(),
            segment.p1.as_tuple(),
            ray[0],
            ray[1],
        )
    else:
        curve = [p.as_tuple() for p in segment.points]
        hits = curveLineIntersections(curve, ray)
    out: list[tuple[float, float]] = []
    for hit in hits:
        if -_T_EPS <= float(hit.t1) <= 1.0 + _T_EPS and -_T_EPS <= float(hit.t2) <= 1.0 + _T_EPS:
            out.append((float(hit.pt[0]), float(hit.pt[1])))
    return out
