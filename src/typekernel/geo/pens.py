"""Drawing an ``Outline`` into a fontTools pen.

This is the one-way bridge from kernel geometry to the pen protocol that every
font tool speaks. It is deliberately dumb: it replays segments as
``moveTo``/``lineTo``/``curveTo``/``closePath`` and never resamples anything. A
cubic goes out as a cubic; only a caller that explicitly asks for quadratic
conversion (``convert_quadratic``) or sampling may reduce it.

Open contours are ended with ``endPath`` rather than ``closePath``, so the pen
learns the same closure fact the ``Contour`` carries. Contours with no segments
are skipped: there is no geometry to replay, and a bare ``moveTo``/``closePath``
pair would invent a degenerate contour the model never held.
"""

from __future__ import annotations

from fontTools.pens.basePen import AbstractPen

from typekernel.geo.outline import Outline
from typekernel.geo.segment import CubicSegment


def draw_outline(outline: Outline, pen: AbstractPen) -> None:
    """Replay ``outline`` into ``pen`` without flattening any curve."""
    for contour in outline.contours:
        if not contour.segments:
            continue
        pen.moveTo(contour.segments[0].points[0].as_tuple())
        for segment in contour.segments:
            if isinstance(segment, CubicSegment):
                pen.curveTo(
                    segment.p1.as_tuple(),
                    segment.p2.as_tuple(),
                    segment.p3.as_tuple(),
                )
            else:
                pen.lineTo(segment.p1.as_tuple())
        if contour.closed:
            pen.closePath()
        else:
            pen.endPath()
