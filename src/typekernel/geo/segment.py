"""Segments — the cubic-first building blocks of a contour.

Two segment types exist in design space, and only two:

``LineSegment(p0, p1)``
    A straight segment. Both ``p0`` and ``p1`` are on-curve; a line carries no
    off-curve control points.

``CubicSegment(p0, p1, p2, p3)``
    A cubic Bézier. ``p0`` and ``p3`` are on-curve endpoints; ``p1`` and ``p2``
    are off-curve control points, which carry the curvature and the handles
    that a polyline approximation would discard.

There is deliberately **no quadratic segment type**. Quadratics are a compile
artefact, not a design truth: they enter the system only as the output of the
cu2qu bridge in ``convert_quadratic``, which reports its error budget. No part
of the design layer may require or store a quadratic.

There is likewise **no polyline or polygon segment type**. Sampling a cubic
into straight lines is a lossy rendering step, never a canonical contour, so it
gets no type to hide behind.

Bézier mathematics is not reimplemented here. ``fontTools.misc.bezierTools``
already offers ``calcCubicBounds(pt1, pt2, pt3, pt4)``, ``splitCubicAtT`` and
``curveCurveIntersections(curve1, curve2)`` over flat point tuples, so a
segment's job is to hold typed :class:`~typekernel.geo.point.Point` values and
hand tuples to those functions.

Public segment API:

``LineSegment.points -> tuple[Point, Point]``
``CubicSegment.points -> tuple[Point, Point, Point, Point]``
    The segment's points in order, ``p0`` first.

``kind -> Literal["line", "cubic"]``
    Discriminator, so a contour can hold a heterogeneous sequence of segments.

The plain-tuple form that fontTools helpers and pens consume is derived from
``points`` through :meth:`Point.as_tuple` at the pen and convert boundary, so
no separate tuple accessor is kept on the segments themselves.

Open questions recorded at the geo public API gate
------------------------------
1. A shared ``Segment`` protocol or alias, so ``Contour`` can hold a
   heterogeneous ``tuple[LineSegment | CubicSegment, ...]`` and still type
   check.
2. Whether a joint's smoothness belongs on the segment or is derived at the
   contour level from control-point collinearity. Storing it duplicates
   information that can drift out of sync with the geometry.
3. Whether degenerate segments (``p0 == p1``) are rejected, normalised, or
   tolerated.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from typekernel.geo.point import Point


@dataclass(frozen=True, slots=True)
class LineSegment:
    """A straight segment between two on-curve points.

    Attributes:
        p0: On-curve start point.
        p1: On-curve end point.
    """

    p0: Point
    p1: Point

    @property
    def points(self) -> tuple[Point, Point]:
        """The segment's points in order, ``p0`` first."""
        return (self.p0, self.p1)

    @property
    def kind(self) -> Literal["line"]:
        """Discriminator identifying this segment as a straight line."""
        return "line"


@dataclass(frozen=True, slots=True)
class CubicSegment:
    """A cubic Bézier segment: two on-curve endpoints, two off-curve controls.

    Attributes:
        p0: On-curve start point.
        p1: Off-curve control point governing the tangent at ``p0``.
        p2: Off-curve control point governing the tangent at ``p3``.
        p3: On-curve end point.
    """

    p0: Point
    p1: Point
    p2: Point
    p3: Point

    @property
    def points(self) -> tuple[Point, Point, Point, Point]:
        """The segment's points in order, ``p0`` first."""
        return (self.p0, self.p1, self.p2, self.p3)

    @property
    def kind(self) -> Literal["cubic"]:
        """Discriminator identifying this segment as a cubic Bézier."""
        return "cubic"
