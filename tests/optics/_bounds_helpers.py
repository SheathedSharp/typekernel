"""Test-only outline y-extrema helpers (not part of production optics)."""

from __future__ import annotations

from typekernel.geo.outline import Outline, bounds


def outline_ymax(outline: Outline) -> float:
    """Return the control-bounds maximum y of ``outline``."""
    return bounds(outline)[3]


def outline_ymin(outline: Outline) -> float:
    """Return the control-bounds minimum y of ``outline``."""
    return bounds(outline)[1]
