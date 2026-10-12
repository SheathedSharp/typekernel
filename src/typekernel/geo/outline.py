"""Outline — a design-space shape made of contours.

An ``Outline`` is a tuple of :class:`~typekernel.geo.contour.Contour` values.
It is the largest geometry object in the kernel and the thing every later layer
consumes: the optics layer transforms it, the compile layer serialises it.

What it deliberately is *not*:

- **Not a glyph.** There is no glyph name, no Unicode value and no advance
  width here. Those are identity and metrics, not geometry; folding them in
  would make a pure shape depend on font bookkeeping. A glyph is a later
  binding of an outline to a name and to metrics.
- **Not font-unit quantised.** Coordinates stay ``float``; rounding is an
  explicit, separate step.
- **Not polyline-backed.** Contours hold cubic and line segments; see
  ``contour``.

API frozen by P0-012, implemented by P0-013:

``Outline(contours: tuple[Contour, ...])``
    Immutable value type.

``Outline.contour_count -> int``
    Number of contours in the shape.

``Outline.iter_segments() -> Iterator[LineSegment | CubicSegment]``
    Yield every segment of every contour, in contour order. This flattens away
    which contour a segment came from; read ``contours`` when that matters.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from typekernel.geo.contour import Contour
from typekernel.geo.segment import CubicSegment, LineSegment


@dataclass(frozen=True, slots=True)
class Outline:
    """A design-space shape: an ordered tuple of contours.

    Attributes:
        contours: The contours that make up the shape.
    """

    contours: tuple[Contour, ...]

    @property
    def contour_count(self) -> int:
        """Number of contours in the shape."""
        return len(self.contours)

    def iter_segments(self) -> Iterator[LineSegment | CubicSegment]:
        """Yield every segment of every contour, in contour order."""
        for contour in self.contours:
            yield from contour.segments
