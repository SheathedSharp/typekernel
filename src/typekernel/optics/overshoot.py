"""Vertical overshoot for round and sharp extrema.

``apply_overshoot`` shifts top and bottom extrema past alignment zones by the
amounts in :class:`~typekernel.optics.context.OpticalContext`. This is an
optical correction, not a stroke expand or pen-radius weight.
"""

from __future__ import annotations

from typing import Literal

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.context import OpticalContext

OvershootKind = Literal["round", "sharp"]


def apply_overshoot(
    outline: Outline,
    ctx: OpticalContext,
    kind: OvershootKind = "round",
) -> Outline:
    """Return a new outline with vertical extrema shifted by overshoot.

    Round kinds use ``ctx.overshoot_round``; sharp kinds use
    ``ctx.overshoot_sharp``. Top on-curve extrema move up by that amount;
    bottom on-curve extrema move down.

    Minimal strategy (v0):

    1. Collect every on-curve point (line endpoints; cubic ``p0`` / ``p3``).
    2. Take the outline-wide max and min ``y`` among those on-curve points.
    3. Rebuild every segment: on-curve points that sit exactly at that max
       (resp. min) ``y`` are offset by ``+amount`` (resp. ``-amount``).
    4. **Naive control-handle handling:** off-curve controls that already share
       the same extrema ``y`` are shifted by the same amount so flat top/bottom
       handles on a round ``O`` stay horizontal. Controls at other ``y`` values
       are left alone. This is deliberately naive — it does not re-fit
       curvature or preserve handle ratios beyond that.

    The input outline is never mutated.
    """
    amount = ctx.overshoot_round if kind == "round" else ctx.overshoot_sharp
    if amount == 0.0:
        return outline

    on_curve_ys = _on_curve_ys(outline)
    if not on_curve_ys:
        return outline

    ymax = max(on_curve_ys)
    ymin = min(on_curve_ys)

    new_contours: list[Contour] = []
    for contour in outline.contours:
        new_segments: list[LineSegment | CubicSegment] = []
        for segment in contour.segments:
            new_segments.append(_shift_segment(segment, ymax, ymin, amount))
        new_contours.append(Contour(tuple(new_segments), closed=contour.closed))
    return Outline(tuple(new_contours))


def _on_curve_ys(outline: Outline) -> list[float]:
    ys: list[float] = []
    for segment in outline.iter_segments():
        if isinstance(segment, LineSegment):
            ys.append(segment.p0.y)
            ys.append(segment.p1.y)
        else:
            ys.append(segment.p0.y)
            ys.append(segment.p3.y)
    return ys


def _shift_point(point: Point, ymax: float, ymin: float, amount: float) -> Point:
    if point.y == ymax:
        return Point(point.x, point.y + amount)
    if point.y == ymin:
        return Point(point.x, point.y - amount)
    return point


def _shift_segment(
    segment: LineSegment | CubicSegment,
    ymax: float,
    ymin: float,
    amount: float,
) -> LineSegment | CubicSegment:
    if isinstance(segment, LineSegment):
        return LineSegment(
            _shift_point(segment.p0, ymax, ymin, amount),
            _shift_point(segment.p1, ymax, ymin, amount),
        )
    # Cubic: shift on-curve ends always when they match extrema; also shift
    # off-curve controls that already sit on the extrema y (naive handles).
    return CubicSegment(
        _shift_point(segment.p0, ymax, ymin, amount),
        _shift_point(segment.p1, ymax, ymin, amount),
        _shift_point(segment.p2, ymax, ymin, amount),
        _shift_point(segment.p3, ymax, ymin, amount),
    )
