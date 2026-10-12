"""Cubic → quadratic conversion: the only place quadratics enter the system.

Design space is cubic-first (see ``segment``), so a quadratic never appears as a
design object. Quadratics exist for exactly one reason: TrueType outlines are
quadratic, so the compile path has to produce them. Everything quadratic lives
behind this module, at the compile boundary, and is represented as plain
fontTools point sequences rather than as kernel geometry — there is no
quadratic segment or contour type to mistake for design truth.

The conversion itself is **not** implemented here. It is delegated to
``fontTools.cu2qu``, which the project deliberately does not reimplement. This
module only wraps it and reports what it cost.

Output representation
---------------------
:func:`to_quadratic` returns ``(contours, report)``, where each converted
contour is a :class:`QuadraticContour` holding **one quadratic spline per source
segment**, in the convention ``fontTools.cu2qu`` emits and ``qCurveTo``
consumes:

    ``[on-curve start, off-curve, ..., off-curve, on-curve end]``

Intermediate on-curve points are *implied* as the midpoints of consecutive
off-curve points. That is why a spline of ``n`` quadratics is ``n + 2`` points,
not ``2n + 1``: ``len(points) - 2`` is the quadratic count.

Splines are kept per source segment rather than merged into one long spline.
Merging would be wrong: the implied on-curve point where two splines meet is the
midpoint of their neighbouring off-curve points, which equals the shared
endpoint only when the two tangents happen to be symmetric about it.

Straight segments need no approximation and are emitted exactly as a degenerate
quadratic whose control point is the segment midpoint.

Measuring the error
-------------------
``fontTools.cu2qu`` takes an error budget as *input* and never reports the error
it actually achieved, so ``max_error`` is measured here. For one cubic, cu2qu
splits the curve at uniform parameter values, so the spline's global parameter
equals the source cubic's ``t``; the two can be compared sample by sample. The
reported value is the largest such deviation found, which is a dense,
deterministic **estimate**, not a proof — the budget remains the hard guarantee.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from fontTools.cu2qu.cu2qu import curve_to_quadratic
from fontTools.misc.bezierTools import cubicPointAtT, quadraticPointAtT

from typekernel.geo.outline import Outline
from typekernel.geo.segment import CubicSegment

ERROR_SAMPLES = 1000
"""Parameter samples per cubic when measuring achieved error."""

DEFAULT_BUDGET = 1.0
"""Default error budget, in design-space units, for a 1000 UPM design."""

PointTuple = tuple[float, float]
SplinePoints = tuple[PointTuple, ...]


@dataclass(frozen=True, slots=True)
class ConversionReport:
    """What a cubic → quadratic conversion cost.

    Attributes:
        max_error: Largest measured deviation between a source cubic and the
            quadratic spline produced for it, in design-space units. Measured by
            this module; ``fontTools.cu2qu`` takes an error budget as *input*
            and never reports the error it actually achieved.
        segment_count_in: Number of source segments handed to the converter.
        segment_count_out: Number of quadratic segments produced.
        budget: The error budget the conversion was permitted to spend.
    """

    max_error: float
    segment_count_in: int
    segment_count_out: int
    budget: float


@dataclass(frozen=True, slots=True)
class QuadraticContour:
    """A contour converted to quadratics, one spline per source segment.

    This is a compile-boundary artefact, not design-space geometry: it
    deliberately does not reuse ``Contour``/``CubicSegment``, so it can never be
    mistaken for the design truth it was derived from.

    Attributes:
        splines: One quadratic spline per source segment, each in the
            ``qCurveTo`` convention ``[on, off, ..., off, on]`` with implied
            intermediate on-curve points.
        closed: Whether the source contour was closed.
    """

    splines: tuple[SplinePoints, ...]
    closed: bool

    @property
    def quadratic_count(self) -> int:
        """Total number of quadratic segments across all splines."""
        return sum(len(spline) - 2 for spline in self.splines)


def to_quadratic(
    outline: Outline, budget: float = DEFAULT_BUDGET
) -> tuple[tuple[QuadraticContour, ...], ConversionReport]:
    """Convert every cubic in ``outline`` to quadratic splines via cu2qu.

    Straight segments are passed through exactly, as a degenerate quadratic.

    Raises:
        fontTools.cu2qu.errors.ApproxNotFoundError: if cu2qu cannot approximate
            a curve within ``budget``. The error is deliberately not swallowed:
            a budget that cannot be met is a fact the caller must see.
    """
    contours: list[QuadraticContour] = []
    segment_count_in = 0
    segment_count_out = 0
    max_error = 0.0

    for contour in outline.contours:
        splines: list[SplinePoints] = []
        for segment in contour.segments:
            segment_count_in += 1
            if isinstance(segment, CubicSegment):
                spline = _convert_cubic(segment, budget)
                max_error = max(max_error, _measure_error(segment, spline))
            else:
                spline = _convert_line(segment.p0.as_tuple(), segment.p1.as_tuple())
            segment_count_out += len(spline) - 2
            splines.append(spline)
        contours.append(QuadraticContour(tuple(splines), contour.closed))

    report = ConversionReport(
        max_error=max_error,
        segment_count_in=segment_count_in,
        segment_count_out=segment_count_out,
        budget=budget,
    )
    return tuple(contours), report


def _convert_cubic(segment: CubicSegment, budget: float) -> SplinePoints:
    """Delegate one cubic to cu2qu and normalise the result to tuples."""
    curve = [point.as_tuple() for point in segment.points]
    spline = curve_to_quadratic(curve, budget, all_quadratic=True)
    return tuple((float(x), float(y)) for x, y in spline)


def _convert_line(start: PointTuple, end: PointTuple) -> SplinePoints:
    """Represent a straight segment exactly, as a degenerate quadratic."""
    mid = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
    return (start, mid, end)


def _midpoint(a: PointTuple, b: PointTuple) -> PointTuple:
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _spline_point_at(spline: SplinePoints, s: float) -> PointTuple:
    """Evaluate an ``[on, off, ..., off, on]`` spline at global ``s`` in [0, 1]."""
    count = len(spline) - 2
    if count < 1:
        raise ValueError("a quadratic spline needs at least three points")
    index = min(int(s * count), count - 1)
    local = s * count - index
    start = spline[0] if index == 0 else _midpoint(spline[index], spline[index + 1])
    end = (
        spline[count + 1]
        if index == count - 1
        else _midpoint(spline[index + 1], spline[index + 2])
    )
    return quadraticPointAtT(start, spline[index + 1], end, local)


def _measure_error(
    segment: CubicSegment, spline: SplinePoints, samples: int = ERROR_SAMPLES
) -> float:
    """Largest sampled deviation between one cubic and its quadratic spline."""
    cubic = [point.as_tuple() for point in segment.points]
    worst = 0.0
    for step in range(samples + 1):
        t = step / samples
        source = cubicPointAtT(*cubic, t)
        approx = _spline_point_at(spline, t)
        worst = max(worst, math.hypot(source[0] - approx[0], source[1] - approx[1]))
    return worst
