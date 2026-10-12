"""geo-kernel: cubic-first geometry.

Cubic Bézier segments are the design truth of a typekernel outline; sampled
polylines are never a canonical contour. Quadratics appear only at the compile
boundary, as the output of :func:`to_quadratic`.

Bézier mathematics is not reimplemented here. It defers to
``fontTools.misc.bezierTools``, ``fontTools.cu2qu`` and the fontTools pens.

This module re-exports the geo-kernel public API frozen by the geo public API gate
(recorded in ``approvals/GATE-P0-API.json``). The list is
deliberately short rather than "everything public": other stable helpers stay in
their own submodules — ``signed_area`` and ``Contour``'s neighbours in
``contour``, ``bounds`` in ``outline``, ``quantize``/``quantize_point`` in
``rounding``, ``QuadraticContour`` in ``convert_quadratic``,
``load_synthetic_outline`` in ``fixtures``, ``boolean_op`` in ``boolean`` — and
must be imported from there.
"""

from __future__ import annotations

from typekernel.geo.contour import Contour
from typekernel.geo.convert_quadratic import ConversionReport, to_quadratic
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.pens import draw_outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

__all__ = [
    "Contour",
    "ConversionReport",
    "CubicSegment",
    "LineSegment",
    "Outline",
    "PathBuilder",
    "Point",
    "draw_outline",
    "to_quadratic",
]
