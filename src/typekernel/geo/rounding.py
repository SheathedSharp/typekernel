"""Explicit, opt-in coordinate quantisation.

Rounding is never applied implicitly anywhere in the kernel. A coordinate is a
``float`` until a caller deliberately asks for fewer digits, because silent
quantisation destroys the curvature and the handles that the cubic-first design
depends on. :class:`~typekernel.geo.path_builder.PathBuilder` in particular does
not round: it hands back exactly the coordinates it was given.

Two different operations are easy to confuse, and this module only implements
the first:

``quantize`` — reduce *decimal precision* of a design-space float, e.g. to make
    sources diffable and stable in text form. Implemented here with Python's
    built-in ``round``.

*Integer font-unit rounding* — snap a design-space coordinate to a whole font
    unit for compilation. That is a **different** operation with a **different**
    tie-breaking rule and must use ``fontTools.misc.roundTools.otRound``, which
    rounds halves away from zero (``otRound(2.5) == 3``, ``otRound(-2.5) == -2``)
    to match OpenType convention. Python's ``round`` rounds halves to even
    (``round(2.5) == 2``), so it must not be used for font units.

Determinism: these helpers depend only on their arguments. There is no random
state, no locale sensitivity and no hidden precision global, so the same input
always produces the same output.
"""

from __future__ import annotations

from typekernel.geo.point import Point

DEFAULT_NDIGITS = 3


def quantize(value: float, ndigits: int = DEFAULT_NDIGITS) -> float:
    """Round ``value`` to ``ndigits`` decimal places.

    Uses Python's built-in ``round``, so ties break toward the even digit
    ("banker's rounding"): ``quantize(0.5, 0) == 0`` and ``quantize(2.5, 0) == 2``.
    That is the right rule for trimming decimal precision, and the *wrong* rule
    for snapping to integer font units — use ``fontTools.misc.roundTools.otRound``
    for that.

    Note that the result is the nearest *representable* float, so it need not
    print with exactly ``ndigits`` digits. This is a formatting aid for stable,
    diffable output, not a fixed-point type.
    """
    return round(value, ndigits)


def quantize_point(point: Point, ndigits: int = DEFAULT_NDIGITS) -> Point:
    """Return a copy of ``point`` with both coordinates quantised.

    The original is untouched; ``Point`` is immutable, so a new value is
    returned.
    """
    return Point(quantize(point.x, ndigits), quantize(point.y, ndigits))
