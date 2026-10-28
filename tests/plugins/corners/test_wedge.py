"""Contract tests for ``plugins.corners.wedge`` (ARCHITECTURE.md 槽位与填充协议)."""

from __future__ import annotations

from tests.plugins.corners.helpers import contour_area_sign, square_with_knee
from typekernel.draw import apply_slots
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners import wedge
from typekernel.system import System


def test_wedge_apply_slots(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    before = contour_area_sign(drawing)
    out = apply_slots(drawing, system, corners={"knee": wedge(size=0.25)}, ends={})
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    assert all(isinstance(s, LineSegment) for s in out.contours[0].segments)
    assert all(s.tag != "knee" for s in out.slots)


def test_wedge_deterministic(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 8.0})
    filler = wedge(size=0.3, depth=0.2)
    a = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    b = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
