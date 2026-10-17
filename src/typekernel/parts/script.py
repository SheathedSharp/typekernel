"""Shared primitives for letter-writing / calligraphy script faces.

Brand glyph skeletons stay in examples. This module is the reusable geometry
and writing-rail layer that examples call before :func:`~typekernel.parts.skeleton.trace_letter`.

Slant is a **coordinate shear** baked into centerlines — not
:func:`~typekernel.parts.italic.slant_composed_glyph` / oblique post-process.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

__all__ = [
    "chaikin_subdivide",
    "entry_rail",
    "exit_rail",
    "shear_xy",
    "slant_shear",
]


def slant_shear(degrees: float) -> float:
    """Horizontal shear factor ``tan(radians(degrees))`` for writing slant."""
    return math.tan(math.radians(degrees))


def shear_xy(x: float, y: float, shear: float) -> tuple[float, float]:
    """Apply writing slant: ``(x + y * shear, y)``."""
    return (x + y * shear, y)


def chaikin_subdivide(
    pts: Sequence[tuple[float, float]], rounds: int = 4
) -> list[tuple[float, float]]:
    """Corner-cutting densify for polyline skeletons (open polylines).

    Endpoints are preserved. ``rounds=0`` returns a copy of ``pts``.
    """
    if rounds < 0:
        raise ValueError("rounds must be >= 0")
    cur: list[tuple[float, float]] = [(float(p[0]), float(p[1])) for p in pts]
    if len(cur) < 2:
        return cur
    for _ in range(rounds):
        nxt: list[tuple[float, float]] = [cur[0]]
        for i in range(len(cur) - 1):
            a, b = cur[i], cur[i + 1]
            nxt.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            nxt.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        nxt.append(cur[-1])
        cur = nxt
    return cur


def entry_rail(
    x0: float,
    x1: float,
    *,
    y: float,
    lift: float,
    dip: float = 6.0,
    start_rise: float = 20.0,
) -> list[tuple[float, float]]:
    """Three-point entry approach into a letter (pre-shear coordinates)."""
    mid = (x0 + x1) / 2.0
    return [(x0, y + start_rise), (mid, y - dip), (x1, lift)]


def exit_rail(
    x0: float,
    x1: float,
    *,
    y: float,
    lift: float,
    dip: float = 6.0,
    end_rise: float = 28.0,
) -> list[tuple[float, float]]:
    """Three-point exit departure from a letter (pre-shear coordinates)."""
    mid = (x0 + x1) / 2.0
    return [(x0, lift * 0.5), (mid, y - dip), (x1, y + end_rise)]
