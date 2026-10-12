"""PathBuilder — a pen-like authoring front end that produces an ``Outline``.

Coordinates are design-space ``float`` values, in the same units as the rest of
the kernel. Nothing here quantises or rounds.

The method names are deliberately camelCase (``moveTo``, ``lineTo``,
``curveTo``, ``closePath``) to mirror the fontTools pen protocol, so that the
builder reads like the pens every font tool already speaks.

``curveTo`` is **cubic**: two off-curve control points followed by the on-curve
endpoint, matching ``CubicSegment(p0, p1, p2, p3)``. There is no quadratic
``curveTo``, and there is no flattening or sampling entry point: curves stay
curves, and polylines are never a design-time output.

Public PathBuilder API:

``moveTo(x: float, y: float) -> None``
    Start a new contour at ``(x, y)``. A contour already in progress is
    finished first, as an *open* contour, the way the pen protocol expects.

``lineTo(x: float, y: float) -> None``
    Append a straight segment ending at ``(x, y)``.

``curveTo(x1, y1, x2, y2, x3, y3) -> None``
    Append a cubic segment: off-curve ``(x1, y1)`` and ``(x2, y2)``, then the
    on-curve endpoint ``(x3, y3)``.

``closePath() -> None``
    Finish the current contour as closed. If the current point is not already
    the contour's start point, an explicit straight segment is appended to
    close the loop, so the resulting ``Contour`` satisfies
    :meth:`Contour.assert_closed_consistent` — a closed contour whose last
    segment does not end where the first begins would be rejected by the very
    model it came from.

``build() -> Outline``
    Snapshot the builder as an ``Outline``. Non-destructive: it neither clears
    nor finalises state, so it is safe to call more than once.

Two policies chosen here and locked by tests:

1. **Open paths are kept.** A contour still in progress when ``build()`` is
   called is included as an *open* ``Contour`` rather than raising. Silently
   dropping it would discard geometry the caller drew, and this kernel exists
   to carry design intent faithfully rather than to guess that a missing
   ``closePath`` was a mistake.
2. **Contours with no segments are not emitted.** ``moveTo`` followed by
   another ``moveTo``, or by ``closePath``, produces no contour: a start point
   with no segments carries no geometry to preserve. (The ``Contour`` type
   itself still permits an empty contour; the builder simply never creates
   one.)

Misuse — ``lineTo``, ``curveTo`` or ``closePath`` with no contour in progress
— raises ``ValueError``.
"""

from __future__ import annotations

from typing import cast

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.path_helpers import (
    arc_cubics,
    ellipse_cubics,
    quarter_circle_cubics,
    rounded_corner_cubics,
    smooth_cubic_controls,
)
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment


class PathBuilder:
    """Accumulates contours and returns an :class:`Outline`."""

    def __init__(self) -> None:
        self._contours: list[Contour] = []
        self._segments: list[LineSegment | CubicSegment] = []
        self._start: Point | None = None
        self._current: Point | None = None

    def moveTo(self, x: float, y: float) -> None:
        """Start a new contour at ``(x, y)``."""
        if self._start is not None:
            self._finish(closed=False)
        start = Point(x, y)
        self._start = start
        self._current = start

    def lineTo(self, x: float, y: float) -> None:
        """Append a straight segment ending at ``(x, y)``."""
        _, current = self._require_contour("lineTo")
        end = Point(x, y)
        self._segments.append(LineSegment(current, end))
        self._current = end

    def curveTo(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        x3: float,
        y3: float,
    ) -> None:
        """Append a cubic segment with off-curve controls and an endpoint."""
        _, current = self._require_contour("curveTo")
        end = Point(x3, y3)
        self._segments.append(
            CubicSegment(current, Point(x1, y1), Point(x2, y2), end)
        )
        self._current = end

    def closePath(self) -> None:
        """Finish the current contour as closed, closing the loop if needed."""
        start, current = self._require_contour("closePath")
        if self._segments and current != start:
            self._segments.append(LineSegment(current, start))
            self._current = start
        self._finish(closed=True)

    def build(self) -> Outline:
        """Snapshot the builder as an :class:`Outline`, without resetting it."""
        contours = list(self._contours)
        if self._segments:
            contours.append(Contour(tuple(self._segments), closed=False))
        return Outline(tuple(contours))


    def arcTo(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        end_angle_deg: float,
        *,
        start_angle_deg: float | None = None,
    ) -> None:
        """Append an elliptical arc ending at ``end_angle_deg`` (CCW from +x).

        If ``start_angle_deg`` is omitted, it is inferred from the current point
        relative to ``(cx, cy)``. Uses :func:`arc_cubics` (cubic pieces ≤ 90°).
        """
        import math

        _, current = self._require_contour("arcTo")
        if start_angle_deg is None:
            start_angle_deg = math.degrees(math.atan2(current.y - cy, current.x - cx))
        cubics = arc_cubics(cx, cy, rx, ry, start_angle_deg, end_angle_deg)
        for p0, p1, p2, p3 in cubics:
            # Snap first p0 to current if close; otherwise lineTo p0.
            if abs(p0.x - current.x) > 1e-6 or abs(p0.y - current.y) > 1e-6:
                self.lineTo(p0.x, p0.y)
                current = p0
            self.curveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
            current = p3

    def quarterCircleTo(
        self,
        cx: float,
        cy: float,
        rx: float,
        ry: float,
        quadrant: int,
    ) -> None:
        """Append one quarter-ellipse cubic (see :func:`quarter_circle_cubics`)."""
        if quadrant not in (0, 1, 2, 3):
            raise ValueError(f"quadrant must be 0..3, got {quadrant}")
        _, current = self._require_contour("quarterCircleTo")
        from typekernel.geo.path_helpers import Quadrant

        p0, p1, p2, p3 = quarter_circle_cubics(
            cx, cy, rx, ry, cast(Quadrant, quadrant)
        )
        if abs(p0.x - current.x) > 1e-6 or abs(p0.y - current.y) > 1e-6:
            self.lineTo(p0.x, p0.y)
        self.curveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)

    def addEllipse(self, cx: float, cy: float, rx: float, ry: float) -> None:
        """Append a closed elliptical contour centred at ``(cx, cy)``."""
        cubics = ellipse_cubics(cx, cy, rx, ry)
        p0 = cubics[0][0]
        self.moveTo(p0.x, p0.y)
        for _, p1, p2, p3 in cubics:
            self.curveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
        self.closePath()

    def roundedCornerTo(
        self,
        corner_x: float,
        corner_y: float,
        end_x: float,
        end_y: float,
        radius: float,
        *,
        continue_to_end: bool = True,
    ) -> None:
        """Line toward a corner, fillet with a cubic, then optionally to the end.

        From the current point through ``(corner_x, corner_y)`` toward
        ``(end_x, end_y)``, replacing the sharp corner with a kappa-scaled fillet.
        When ``continue_to_end`` is False, the pen stops at the fillet exit on the
        outgoing edge (useful when chaining multiple corners toward a shared vertex).
        """
        _, current = self._require_contour("roundedCornerTo")
        start, c1, c2, end, _ = rounded_corner_cubics(
            current, Point(corner_x, corner_y), Point(end_x, end_y), radius
        )
        if abs(start.x - current.x) > 1e-9 or abs(start.y - current.y) > 1e-9:
            self.lineTo(start.x, start.y)
        self.curveTo(c1.x, c1.y, c2.x, c2.y, end.x, end.y)
        if continue_to_end and (
            abs(end_x - end.x) > 1e-9 or abs(end_y - end.y) > 1e-9
        ):
            self.lineTo(end_x, end_y)

    def smoothCurveTo(
        self,
        x3: float,
        y3: float,
        *,
        tangent_out_x: float,
        tangent_out_y: float,
        handle_ratio: float = 1.0 / 3.0,
        tangent_in_x: float | None = None,
        tangent_in_y: float | None = None,
    ) -> None:
        """Append a cubic to ``(x3, y3)`` with G1-friendly handle placement.

        Incoming tangent defaults to the previous segment's outgoing direction.
        ``tangent_out_*`` is the desired direction at the endpoint.
        """
        _, current = self._require_contour("smoothCurveTo")
        if tangent_in_x is None or tangent_in_y is None:
            if not self._segments:
                raise ValueError("smoothCurveTo needs a prior segment or tangent_in_*")
            prev = self._segments[-1]
            if isinstance(prev, LineSegment):
                tin = Point(prev.p1.x - prev.p0.x, prev.p1.y - prev.p0.y)
            else:
                tin = Point(prev.p3.x - prev.p2.x, prev.p3.y - prev.p2.y)
        else:
            tin = Point(tangent_in_x, tangent_in_y)
        p3 = Point(x3, y3)
        p1, p2 = smooth_cubic_controls(
            current, p3, tin, Point(tangent_out_x, tangent_out_y), handle_ratio=handle_ratio
        )
        self.curveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)


    def _require_contour(self, method: str) -> tuple[Point, Point]:
        """Return ``(start, current)``, or raise if no contour is in progress."""
        if self._start is None or self._current is None:
            raise ValueError(f"{method}() requires a preceding moveTo()")
        return self._start, self._current

    def _finish(self, *, closed: bool) -> None:
        """Retire the contour in progress, dropping it if it has no segments."""
        if self._segments:
            self._contours.append(Contour(tuple(self._segments), closed=closed))
        self._segments = []
        self._start = None
        self._current = None
