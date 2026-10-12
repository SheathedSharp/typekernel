"""Loading synthetic golden fixtures into kernel geometry.

Fixtures are plain JSON so they stay diffable and reviewable by hand, which is
the point of a golden file. This module is the only place that knows the
document layout; nothing else should reach into the JSON directly.

Only **geometry** is loaded. ``Outline`` deliberately carries no glyph name and
no units-per-em (see ``outline``), so those fields stay in the document and a
caller that needs them reads the JSON itself. Binding geometry to a name and to
metrics is a later layer's job, not the geometry kernel's.
"""

from __future__ import annotations

import json
from pathlib import Path

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment

CUBIC_VALUES = 8


def load_synthetic_outline(path: str | Path) -> Outline:
    """Load a synthetic fixture document and return its :class:`Outline`.

    Contours are built through the ``Contour`` constructor rather than through
    :class:`~typekernel.geo.path_builder.PathBuilder`: the fixture stores
    explicit cubic control points, including the segment that closes the loop,
    so there is nothing for the builder's implicit closing behaviour to add.

    Raises:
        ValueError: if a cubic does not hold exactly eight numbers, or if a
            contour marked ``closed`` does not actually close, or if
            consecutive cubics do not meet end-to-start.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    contours: list[Contour] = []
    for contour_index, raw_contour in enumerate(data["contours"]):
        segments: list[CubicSegment] = []
        for cubic_index, values in enumerate(raw_contour["cubics"]):
            if len(values) != CUBIC_VALUES:
                raise ValueError(
                    f"contour {contour_index} cubic {cubic_index}: expected "
                    f"{CUBIC_VALUES} numbers, got {len(values)}"
                )
            segments.append(
                CubicSegment(
                    Point(values[0], values[1]),
                    Point(values[2], values[3]),
                    Point(values[4], values[5]),
                    Point(values[6], values[7]),
                )
            )
        contour = Contour(tuple(segments), closed=bool(raw_contour.get("closed", False)))
        contour.assert_closed_consistent()
        contour.assert_segments_continuous()
        contours.append(contour)
    return Outline(tuple(contours))
