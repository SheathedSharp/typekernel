"""Vertical overshoot for round and sharp extrema.

``apply_overshoot`` shifts top and bottom extrema past alignment zones by the
amounts in :class:`~typekernel.optics.context.OpticalContext`. This is an
optical correction, not a stroke expand or pen-radius weight.

By default (``align_to_zones=True``) only points near baseline / x-height /
cap-height are candidates, so a descender foot far below the baseline is not
dragged just because it is the outline-wide ``ymin``. For ``kind="round"``,
only on-curve points with a horizontal cubic handle (classic round extremum)
are shifted — flat feet made of line corners stay put.
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
    *,
    align_to_zones: bool = True,
    zone_band: float | None = None,
) -> Outline:
    """Return a new outline with vertical extrema shifted by overshoot.

    Round kinds use ``ctx.overshoot_round``; sharp kinds use
    ``ctx.overshoot_sharp``. Top candidates move up by that amount; bottom
    candidates move down.

    Args:
        outline: Input geometry (never mutated).
        ctx: Optical parameters (zones + amounts).
        kind: ``"round"`` or ``"sharp"``.
        align_to_zones: When True (default), only points near baseline ``0``,
            ``ctx.x_height``, or ``ctx.cap_height`` are considered. When False,
            uses the outline-wide on-curve ``ymin`` / ``ymax`` (legacy v0).
        zone_band: Half-width of the alignment band. Defaults to
            ``max(amount, 2.0)``.

    Round mode additionally requires a horizontal cubic handle at the point so
    flat polyline feet are not yanked past the baseline.
    """
    amount = ctx.overshoot_round if kind == "round" else ctx.overshoot_sharp
    if amount == 0.0:
        return outline

    band = zone_band if zone_band is not None else max(abs(amount), 2.0)
    top_ys, bottom_ys = _candidate_extrema_ys(
        outline, ctx, kind=kind, align_to_zones=align_to_zones, band=band
    )
    if not top_ys and not bottom_ys:
        return outline

    ymax = max(top_ys) if top_ys else None
    ymin = min(bottom_ys) if bottom_ys else None

    new_contours: list[Contour] = []
    for contour in outline.contours:
        new_segments: list[LineSegment | CubicSegment] = []
        for segment in contour.segments:
            new_segments.append(_shift_segment(segment, ymax, ymin, amount))
        new_contours.append(Contour(tuple(new_segments), closed=contour.closed))
    return Outline(tuple(new_contours))


def _near(y: float, target: float, band: float) -> bool:
    return abs(y - target) <= band


def _on_curve_points(outline: Outline) -> list[Point]:
    points: list[Point] = []
    for segment in outline.iter_segments():
        if isinstance(segment, LineSegment):
            points.append(segment.p0)
            points.append(segment.p1)
        else:
            points.append(segment.p0)
            points.append(segment.p3)
    return points


def _horizontal_handle_ys(outline: Outline) -> set[float]:
    """Y values of on-curve cubic ends that share y with a neighbouring handle."""
    marked: set[float] = set()
    for segment in outline.iter_segments():
        if not isinstance(segment, CubicSegment):
            continue
        if segment.p1.y == segment.p0.y:
            marked.add(segment.p0.y)
        if segment.p2.y == segment.p3.y:
            marked.add(segment.p3.y)
    return marked


def _candidate_extrema_ys(
    outline: Outline,
    ctx: OpticalContext,
    *,
    kind: OvershootKind,
    align_to_zones: bool,
    band: float,
) -> tuple[list[float], list[float]]:
    on_curve = _on_curve_points(outline)
    if not on_curve:
        return [], []

    if kind == "round":
        round_ys = _horizontal_handle_ys(outline)
        eligible = [p for p in on_curve if p.y in round_ys]
        if not eligible:
            # No round extrema detected — do not invent shifts.
            return [], []
    else:
        eligible = on_curve

    if not align_to_zones:
        ys = [p.y for p in eligible]
        return [max(ys)], [min(ys)]

    top_targets = (ctx.x_height, ctx.cap_height)
    baseline = 0.0
    top: list[float] = []
    bottom: list[float] = []
    for p in eligible:
        if any(_near(p.y, t, band) for t in top_targets):
            top.append(p.y)
        if _near(p.y, baseline, band):
            bottom.append(p.y)
    return top, bottom


def _shift_point(
    point: Point,
    ymax: float | None,
    ymin: float | None,
    amount: float,
) -> Point:
    if ymax is not None and point.y == ymax:
        return Point(point.x, point.y + amount)
    if ymin is not None and point.y == ymin:
        return Point(point.x, point.y - amount)
    return point


def _shift_segment(
    segment: LineSegment | CubicSegment,
    ymax: float | None,
    ymin: float | None,
    amount: float,
) -> LineSegment | CubicSegment:
    if isinstance(segment, LineSegment):
        return LineSegment(
            _shift_point(segment.p0, ymax, ymin, amount),
            _shift_point(segment.p1, ymax, ymin, amount),
        )
    return CubicSegment(
        _shift_point(segment.p0, ymax, ymin, amount),
        _shift_point(segment.p1, ymax, ymin, amount),
        _shift_point(segment.p2, ymax, ymin, amount),
        _shift_point(segment.p3, ymax, ymin, amount),
    )
