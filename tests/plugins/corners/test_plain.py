"""Contract tests for ``plugins.corners.plain`` (ARCHITECTURE.md §9.5)."""

from __future__ import annotations

from tests.plugins.corners.helpers import contour_area_sign, square_with_knee
from typekernel.draw import apply_slots
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners import plain
from typekernel.system import System


def test_plain_apply_slots_succeeds_and_stays_closed(system: System) -> None:
    drawing = square_with_knee()
    before_sign = contour_area_sign(drawing)
    out = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    assert len(out.contours) == 1
    assert out.contours[0].closed
    assert contour_area_sign(out) == before_sign
    # plain ≡ unmatched: corner slot remains for later fills / G1 exemption.
    assert any(s.tag == "knee" for s in out.slots)


def test_plain_keeps_sharp_topology(system: System) -> None:
    """Zero trim no-op: original line–line corner, no inserted segments."""
    drawing = square_with_knee()
    out = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    segs = out.contours[0].segments
    assert all(isinstance(s, LineSegment) for s in segs)
    assert len(segs) == len(drawing.contours[0].segments) == 4
    degenerates = [
        s
        for s in segs
        if abs(s.p1.x - s.p0.x) < 1e-9 and abs(s.p1.y - s.p0.y) < 1e-9
    ]
    assert degenerates == []


def test_plain_geometry_matches_unmatched(system: System) -> None:
    """§9.5: explicit plain ≡ unmatched geometry and remaining corner slots."""
    drawing = square_with_knee()
    with_plain = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    unmatched = apply_slots(drawing, system, corners={}, ends={})
    assert [type(s).__name__ for s in with_plain.contours[0].segments] == [
        type(s).__name__ for s in unmatched.contours[0].segments
    ]
    assert len(with_plain.contours[0].segments) == len(unmatched.contours[0].segments)
    assert {s.tag for s in with_plain.slots} == {s.tag for s in unmatched.slots}


def test_plain_deterministic_segment_kinds(system: System) -> None:
    drawing = square_with_knee()
    filler = plain()
    a = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    b = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    kinds_a = tuple(type(s).__name__ for s in a.contours[0].segments)
    kinds_b = tuple(type(s).__name__ for s in b.contours[0].segments)
    assert kinds_a == kinds_b


def test_plain_ignores_system_and_meta(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 40.0})
    out = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    assert len(out.contours[0].segments) == 4
