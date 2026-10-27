"""Shared helpers for corner-plugin contract tests (synthetic geometry only)."""

from __future__ import annotations

from typekernel.draw import Writer
from typekernel.geo.contour import signed_area
from typekernel.system import Overshoot, System, Zones


def make_system(*, stem: float = 80.0) -> System:
    return System(
        upm=1000,
        zones=Zones(x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": stem},
    )


def square_with_knee(*, meta: dict[str, float] | None = None):
    """Unit square, CCW, corner slot ``knee`` at (20, 0)."""
    w = Writer().start((0, 0)).line((20, 0))
    if meta:
        w = w.corner("knee", **meta)
    else:
        w = w.corner("knee")
    return w.line((20, 20)).line((0, 20)).close().build()


def contour_area_sign(drawing) -> float:
    area = signed_area(drawing.contours[0])
    if area > 0:
        return 1.0
    if area < 0:
        return -1.0
    return 0.0
