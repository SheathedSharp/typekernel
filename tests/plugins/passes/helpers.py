"""Helpers for pass-plugin contract tests."""

from __future__ import annotations

from typekernel.draw import Writer
from typekernel.system import Overshoot, System, Zones


def make_system(*, stem: float = 80.0, round_os: float = 12.0, pointed_os: float = 10.0) -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=round_os, pointed=pointed_os),
        stem={"lc": stem},
    )


def round_rect_at_x_height(*, x: float = 500.0, w: float = 40.0, h: float = 40.0):
    """Axis-aligned box whose top sits on the x-height zone."""
    half = w / 2.0
    y0 = x - h
    return (
        Writer()
        .start((-half, y0))
        .line((half, y0))
        .line((half, x))
        .node("top")
        .line((-half, x))
        .node("top_left")
        .close()
        .build()
    )
