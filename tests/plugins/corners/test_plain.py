"""Contract tests for ``plugins.corners.plain`` (ARCHITECTURE.md §9.5)."""

from __future__ import annotations

import pytest

from tests.plugins.corners.helpers import (
    contour_area_sign,
    corner_slot_tags,
    line_curve_knee,
    segment_kind_sequence,
    square_with_knee,
)
from typekernel.draw import apply_slots
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners import plain
from typekernel.system import System


def _plain_vs_unmatched(drawing, system: System):
    with_plain = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    unmatched = apply_slots(drawing, system, corners={}, ends={})
    return with_plain, unmatched


@pytest.mark.parametrize("fixture", [square_with_knee, line_curve_knee], ids=["line_line", "line_curve"])
def test_plain_equals_unmatched_geometry_and_slots(system: System, fixture) -> None:
    """§9.5: ``apply_slots(..., plain())`` ≡ ``apply_slots(..., {})``.

    Same segment count, same segment-kind sequence, same remaining corner tags.
    Covers curve-adjacent knees so a zero-length insert cannot hide behind the
    defensive G1 skip.
    """
    drawing = fixture()
    with_plain, unmatched = _plain_vs_unmatched(drawing, system)
    assert len(with_plain.contours[0].segments) == len(unmatched.contours[0].segments)
    assert segment_kind_sequence(with_plain) == segment_kind_sequence(unmatched)
    assert corner_slot_tags(with_plain) == corner_slot_tags(unmatched)
    assert "knee" in corner_slot_tags(with_plain)
    # Points must match (not only kinds) so noop did not move geometry.
    for a, b in zip(
        with_plain.contours[0].segments, unmatched.contours[0].segments, strict=True
    ):
        assert type(a) is type(b)
        if isinstance(a, LineSegment):
            assert abs(a.p0.x - b.p0.x) < 1e-9 and abs(a.p0.y - b.p0.y) < 1e-9
            assert abs(a.p1.x - b.p1.x) < 1e-9 and abs(a.p1.y - b.p1.y) < 1e-9


def test_plain_apply_slots_succeeds_and_stays_closed(system: System) -> None:
    drawing = square_with_knee()
    before_sign = contour_area_sign(drawing)
    out = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    assert len(out.contours) == 1
    assert out.contours[0].closed
    assert contour_area_sign(out) == before_sign
    assert "knee" in corner_slot_tags(out)


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
    """Alias kept for older call sites; delegates to the parametrized contract."""
    drawing = square_with_knee()
    with_plain, unmatched = _plain_vs_unmatched(drawing, system)
    assert segment_kind_sequence(with_plain) == segment_kind_sequence(unmatched)
    assert len(with_plain.contours[0].segments) == len(unmatched.contours[0].segments)
    assert corner_slot_tags(with_plain) == corner_slot_tags(unmatched)


def test_plain_on_curve_adjacent_does_not_raise(system: System) -> None:
    """Explicit plain on line–curve knee must not raise ContinuityError."""
    drawing = line_curve_knee()
    out = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    assert len(out.contours[0].segments) == len(drawing.contours[0].segments)
    assert "knee" in corner_slot_tags(out)


def test_plain_deterministic_segment_kinds(system: System) -> None:
    drawing = square_with_knee()
    filler = plain()
    a = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    b = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    assert segment_kind_sequence(a) == segment_kind_sequence(b)


def test_plain_ignores_system_and_meta(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 40.0})
    out = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    assert len(out.contours[0].segments) == 4
