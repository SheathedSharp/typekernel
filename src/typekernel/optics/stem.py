"""Stem measurement and diagonal optical compensation.

Vertical and oriented stem widths are measured from designed outline
intersections (ray spans), never taken from a stroke-width constant as a
weight axis. Diagonal compensation returns a *construction* thickness so a
slanted bar matches the apparent weight of a vertical stem — it is not
``buffer`` / pen-radius weight.
"""

from __future__ import annotations

import math

from fontTools.misc.bezierTools import curveLineIntersections, lineLineIntersections

from typekernel.geo.outline import Outline, bounds
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.context import OpticalContext

_T_EPS = 1e-6


def measure_vertical_stem(outline: Outline, x: float) -> float | None:
    """Measure the width of the vertical stem nearest to ``x``.

    Casts a **horizontal** probe ray through the vertical mid-point of the
    outline's control-point bounds. Intersection ``x`` values with every
    segment are collected and sorted. Under a simple even-odd crossing model,
    consecutive pairs ``(xs[0], xs[1])``, ``(xs[2], xs[3])``, … are treated as
    filled stem spans. The span that contains ``x`` is returned as its width;
    if none contains ``x``, returns ``None``.
    """
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return None

    y_probe = (min_y + max_y) / 2.0
    margin = max(1.0, (max_x - min_x) * 0.05 + 1.0)
    ray = [(min_x - margin, y_probe), (max_x + margin, y_probe)]

    xs: list[float] = []
    for segment in outline.iter_segments():
        xs.extend(_intersection_xs(segment, ray))

    if len(xs) < 2:
        return None

    unique = _merge_sorted(xs)
    for i in range(0, len(unique) - 1, 2):
        left = unique[i]
        right = unique[i + 1]
        if left <= x <= right:
            width = right - left
            return width if width > 0.0 else None
    return None


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
            # Parameter along the normal axis from origin
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

    This is a construction aid for :func:`~typekernel.parts.primitives.diagonal_stem`,
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


def equalize_vertical_stems(
    outline: Outline,
    target_width: float,
    ctx: OpticalContext,
) -> Outline:
    """Equalize vertical stem widths toward ``target_width``.

    Reserved API. Real equalization redistributes designed deltas; it must
    never be faked as stroke expand / pen-radius weight. Not implemented in
    this phase.
    """
    del outline, target_width, ctx
    raise NotImplementedError(
        "equalize_vertical_stems is reserved; designed-delta equalization "
        "is not implemented yet and must not be faked via stroke expand"
    )


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
