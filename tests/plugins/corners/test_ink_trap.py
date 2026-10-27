"""Contract tests for ``plugins.corners.ink_trap`` (ARCHITECTURE.md §9.5)."""

from __future__ import annotations

from tests.plugins.corners.helpers import contour_area_sign, square_with_knee
from typekernel.draw import apply_slots
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners import ink_trap
from typekernel.system import System


def test_ink_trap_curved_apply_slots(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    before = contour_area_sign(drawing)
    out = apply_slots(
        drawing, system, corners={"knee": ink_trap(size=0.12)}, ends={}
    )
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    segs = out.contours[0].segments
    assert all(isinstance(s, LineSegment) for s in segs)
    # Curved trap inserts a multi-segment polyline (> 2 fill segs).
    assert len(segs) > 5
    assert all(s.tag != "knee" for s in out.slots)


def test_ink_trap_straight_variant(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    before = contour_area_sign(drawing)
    out = apply_slots(
        drawing,
        system,
        corners={"knee": ink_trap(size=0.15, curved=False)},
        ends={},
    )
    assert contour_area_sign(out) == before
    assert all(isinstance(s, LineSegment) for s in out.contours[0].segments)


def test_ink_trap_deterministic(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    filler = ink_trap(size=0.1)
    a = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    b = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
