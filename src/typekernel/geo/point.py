"""Point — the immutable 2D coordinate of the geo-kernel.

A ``Point`` is deliberately the thinnest type in the kernel: an immutable pair
of floats, and nothing else. It carries no identity, no segment role and no
on/off-curve flag, so a cubic control point and an on-curve anchor are the same
kind of value here; role is decided by the segment layer above.

Coordinates stay ``float`` throughout. Quantising to integers is a separate,
explicit step (see the rounding module) and must never happen implicitly — a
``Point`` that silently rounds would destroy the curvature this kernel exists
to preserve.

Interop: ``fontTools.misc.bezierTools`` and every pen in ``fontTools.pens``
consume plain ``tuple[float, float]`` pairs. :meth:`Point.as_tuple` is the
bridge to them; the Bézier math itself is not reimplemented here.

Public point API:

``Point(x: float, y: float)``
    Immutable value type (``frozen=True, slots=True``). Hashable, so points can
    key a set or dict — useful for deduplicating contour endpoints later.

``Point.as_tuple() -> tuple[float, float]``
    Return ``(x, y)`` in the form fontTools helpers and pens accept.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Point:
    """An immutable 2D point.

    Attributes:
        x: Horizontal coordinate.
        y: Vertical coordinate.

    Frozen on purpose: a ``Point`` is a value, so mutating one in place is a
    bug rather than an operation — transformations return new points. ``slots``
    keeps instances small (outlines hold a great many of them) and stops
    ad-hoc attributes from being attached to a value type.
    """

    x: float
    y: float

    def as_tuple(self) -> tuple[float, float]:
        """Return the point as ``(x, y)``.

        This is the representation expected by ``fontTools.misc.bezierTools``
        helpers and by pens in ``fontTools.pens``.
        """
        return (self.x, self.y)
