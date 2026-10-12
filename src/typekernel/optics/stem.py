"""Stem measurement and equalization stubs.

Vertical stem width is measured from designed outline intersections, never
taken from a stroke-width constant or buffer radius.
"""

from __future__ import annotations

from fontTools.misc.bezierTools import curveLineIntersections, lineLineIntersections

from typekernel.geo.outline import Outline, bounds
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.context import OpticalContext


def measure_vertical_stem(outline: Outline, x: float) -> float | None:
    """Measure the width of the vertical stem nearest to ``x``.

    Casts a **horizontal** probe ray through the vertical mid-point of the
    outline's control-point bounds. Intersection ``x`` values with every
    segment are collected and sorted. Under a simple even-odd crossing model,
    consecutive pairs ``(xs[0], xs[1])``, ``(xs[2], xs[3])``, … are treated as
    filled stem spans. The span that contains ``x`` is returned as its width;
    if none contains ``x``, returns ``None``.

    ``x`` therefore selects *which* vertical stem to read when several exist
    (for example the left vs right bar of an ``H``).
    """
    try:
        min_x, min_y, max_x, max_y = bounds(outline)
    except ValueError:
        return None

    y_probe = (min_y + max_y) / 2.0
    # Ray long enough to clear the control box with a small margin.
    margin = max(1.0, (max_x - min_x) * 0.05 + 1.0)
    ray_start = (min_x - margin, y_probe)
    ray_end = (max_x + margin, y_probe)
    ray = [ray_start, ray_end]

    xs: list[float] = []
    for segment in outline.iter_segments():
        xs.extend(_intersection_xs(segment, ray))

    if len(xs) < 2:
        return None

    unique = sorted(set(xs))
    # Even-odd pairing: (0,1), (2,3), ... — gaps between spans are not stems.
    for i in range(0, len(unique) - 1, 2):
        left = unique[i]
        right = unique[i + 1]
        if left <= x <= right:
            width = right - left
            return width if width > 0.0 else None
    return None


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


def _intersection_xs(
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
        return [float(hit.pt[0]) for hit in hits]

    curve = [p.as_tuple() for p in segment.points]
    hits = curveLineIntersections(curve, ray)
    return [float(hit.pt[0]) for hit in hits]
