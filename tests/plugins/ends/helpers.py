"""Synthetic helpers for end-plugin contract tests."""

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


def stem_with_tip_end(*, stem: float = 10.0, height: float = 40.0):
    """Vertical stem rectangle with an ``end`` slot on the top cut."""
    half = stem / 2.0
    return (
        Writer()
        .start((-half, 0.0))
        .line((-half, height))
        .end("tip", stem=stem)
        .line((half, height))
        .line((half, 0.0))
        .close()
        .build()
    )


def contour_area_sign(drawing) -> float:
    area = signed_area(drawing.contours[0])
    if area > 0:
        return 1.0
    if area < 0:
        return -1.0
    return 0.0
