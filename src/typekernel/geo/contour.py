"""Contour — an ordered boundary built from cubic and line segments.

A ``Contour`` is a sequence of segments in drawing order, plus a flag saying
whether the boundary closes back on itself. It is the first place where
segments become a *shape*.

Two rules define it:

1. **Cubic and line segments only.** A contour holds
   :class:`~typekernel.geo.segment.LineSegment` and
   :class:`~typekernel.geo.segment.CubicSegment` values. There is no quadratic
   member and no polyline member; see ``segment`` for why.
2. **It must never store a raw float point list as its truth.** A
   ``list[tuple[float, float]]`` of sampled vertices is a rendering artefact.
   If a contour carried one as its canonical data, the curvature and the
   handles would be gone and every downstream layer would be reasoning about
   the wrong object. Sampling may be *derived* on demand; it may not be stored.

API frozen by P0-009, implemented by P0-010:

``Contour(segments: tuple[LineSegment | CubicSegment, ...], closed: bool)``
    Immutable value type. ``segments`` is a tuple rather than a list, so a
    contour cannot be mutated in place after it is built.

``Contour.is_empty -> bool``
    True when the contour holds no segments.

``Contour.assert_closed_consistent() -> None``
    Raise if ``closed`` is set but the last segment does not end where the
    first begins. v0 compares endpoints by exact equality; a tolerance-based
    closure check is deliberately deferred.

Note for GATE-P0-API: the canonical ``Segment`` alias belongs in ``segment``,
not here, but P0-009/P0-010 may only touch ``contour.py``, so the union is
spelled out inline until a task is allowed to move it.
"""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment


@dataclass(frozen=True, slots=True)
class Contour:
    """An ordered, cubic-first boundary.

    Attributes:
        segments: The boundary segments, in drawing order.
        closed: Whether the boundary closes back on itself.
    """

    segments: tuple[LineSegment | CubicSegment, ...]
    closed: bool = False

    @property
    def is_empty(self) -> bool:
        """True when the contour holds no segments."""
        return not self.segments

    def assert_closed_consistent(self) -> None:
        """Check that a contour flagged ``closed`` really does close.

        v0 compares the first segment's start point with the last segment's end
        point using exact equality. Coordinates are floats, so a contour that
        closes only "to within rounding" is rejected here; a tolerance-based
        check is deferred until the rounding layer exists. An empty contour has
        no endpoints to compare and is therefore accepted.

        Raises:
            ValueError: if ``closed`` is set and the endpoints disagree.
        """
        if not self.closed or not self.segments:
            return
        start = self.segments[0].points[0]
        end = self.segments[-1].points[-1]
        if start != end:
            raise ValueError(
                "closed contour does not close: starts at "
                f"{start.as_tuple()}, ends at {end.as_tuple()}"
            )


def _on_curve_points(contour: Contour) -> tuple[Point, ...]:
    """Return the contour's on-curve points, in order.

    For a closed contour these are the segment start points, and the closing
    edge back to the first point is implicit. For an open contour the final
    endpoint is appended, so the sequence still describes a drawable polyline.
    """
    if not contour.segments:
        return ()
    points = [segment.points[0] for segment in contour.segments]
    if not contour.closed:
        points.append(contour.segments[-1].points[-1])
    return tuple(points)


def signed_area(contour: Contour) -> float:
    """Signed area of the polygon through the contour's on-curve points.

    Sign convention follows the standard mathematical orientation with ``y``
    pointing up: **positive is counter-clockwise, negative is clockwise**. Zero
    means degenerate (fewer than three distinct on-curve points).

    This is an **orientation helper, not the contour's area.** It is the
    shoelace formula over on-curve points only, so it ignores how far cubic
    handles bow the edges outward: the magnitude is a lower bound on the true
    enclosed area and must not be reported as one. The *sign*, which is what
    callers need in order to tell an outer contour from a counter, matches the
    real orientation for any non-degenerate contour.

    If an exact signed area is ever needed, use
    ``fontTools.pens.areaPen.AreaPen`` — it walks the actual curves. It is not
    used here because orientation only needs the cheap polygon pass.
    """
    points = _on_curve_points(contour)
    if len(points) < 3:
        return 0.0
    total = 0.0
    for current, following in zip(points, (*points[1:], points[0]), strict=True):
        total += current.x * following.y - following.x * current.y
    return total / 2.0
