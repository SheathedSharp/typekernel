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

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
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
