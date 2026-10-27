"""Contract tests for ``plugins.ends.ball``."""

from __future__ import annotations

from tests.plugins.ends.helpers import contour_area_sign, stem_with_tip_end
from typekernel.draw import apply_slots
from typekernel.geo.segment import LineSegment
from typekernel.plugins.ends import ball
from typekernel.system import System


def test_ball_apply_slots(system: System) -> None:
    drawing = stem_with_tip_end()
    before = contour_area_sign(drawing)
    out = apply_slots(drawing, system, corners={}, ends={"tip": ball()})
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    assert all(isinstance(s, LineSegment) for s in out.contours[0].segments)
    assert len(out.contours[0].segments) > 4
    assert all(s.tag != "tip" for s in out.slots)


def test_ball_deterministic(system: System) -> None:
    drawing = stem_with_tip_end()
    filler = ball(radius=6.0)
    a = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    b = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
