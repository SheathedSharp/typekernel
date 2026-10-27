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
    """Unit square, CCW, corner slot ``knee`` at (20, 0) — line–line join."""
    w = Writer().start((0, 0)).line((20, 0))
    if meta:
        w = w.corner("knee", **meta)
    else:
        w = w.corner("knee")
    return w.line((20, 20)).line((0, 20)).close().build()


def line_curve_knee(*, meta: dict[str, float] | None = None):
    """CCW contour: horizontal line into ``knee``, then a cubic leaving upward.

    Curve-adjacent corner: a zero-length insert next to the cubic would be a
    line–curve join and would need the defensive G1 skip to pass. Contract
    fillers (plain / unmatched / radius→0) must leave geometry unchanged
    without relying on that skip (§9.5).

    ``top.r`` is a separate sharp corner so Writer write-time G1 stays valid
    at the cubic→horizontal join; only ``knee`` is under test.
    """
    w = Writer().start((0, 0)).line((20, 0))
    if meta:
        w = w.corner("knee", **meta)
    else:
        w = w.corner("knee")
    # Outgoing cubic: start (20,0), leave roughly upward, end (20,20).
    return (
        w.curve((20, 8), (20, 14), (20, 20))
        .corner("top.r")
        .line((0, 20))
        .line((0, 0))
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


def segment_kind_sequence(drawing) -> tuple[str, ...]:
    return tuple(type(s).__name__ for s in drawing.contours[0].segments)


def corner_slot_tags(drawing) -> set[str]:
    return {s.tag for s in drawing.slots if s.kind == "corner"}
