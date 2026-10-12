"""Oblique (shear) versus true italic (designed) — explicit API split.

Shear is a mechanical transform. True italic is a redesigned master. Mixing
the two names is a long-standing source of bad type; this module keeps them
apart on purpose.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment


@dataclass(frozen=True, slots=True)
class ObliqueTransform:
    """Affine horizontal shear by ``angle_degrees`` from the vertical.

    Positive angles lean the shape to the right (x increases with y). This is
    **oblique**, not italic.
    """

    angle_degrees: float

    def apply(self, outline: Outline) -> Outline:
        """Return a new outline sheared by this transform's angle."""
        shear = math.tan(math.radians(self.angle_degrees))

        def shift(point: Point) -> Point:
            return Point(point.x + point.y * shear, point.y)

        new_contours: list[Contour] = []
        for contour in outline.contours:
            new_segments: list[LineSegment | CubicSegment] = []
            for segment in contour.segments:
                moved = tuple(shift(point) for point in segment.points)
                if segment.kind == "line":
                    new_segments.append(LineSegment(moved[0], moved[1]))
                else:
                    new_segments.append(CubicSegment(moved[0], moved[1], moved[2], moved[3]))
            new_contours.append(Contour(tuple(new_segments), closed=contour.closed))
        return Outline(tuple(new_contours))


@dataclass(frozen=True, slots=True)
class ItalicDesign:
    """Placeholder for a true italic master (designed, not sheared).

    Applying this raises until a real italic design path exists. Do not use
    :class:`ObliqueTransform` under an italic name.
    """

    def apply(self, outline: Outline) -> Outline:
        """Not implemented — true italic is a designed master, not a shear."""
        raise NotImplementedError(
            "ItalicDesign.apply is not implemented: true italic requires "
            "designed masters, not ObliqueTransform shear"
        )
