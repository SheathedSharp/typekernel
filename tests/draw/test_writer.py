"""Writer / Drawing continuity and winding tests (§9.9)."""

from __future__ import annotations

import pytest

from typekernel.draw import ContinuityError, Fragment, Writer
from typekernel.geo.contour import signed_area
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment


def test_writer_rectangle_four_lines_ccw_no_corner_slots() -> None:
    d = (
        Writer()
        .start((0, 0))
        .line((10, 0))
        .line((10, 8))
        .line((0, 8))
        .close()
        .build()
    )
    assert len(d.contours) == 1
    assert len(d.contours[0].segments) == 4
    assert all(s.kind == "line" for s in d.contours[0].segments)
    assert signed_area(d.contours[0]) > 0
    assert d.roles == ("ink",)
    assert d.slots == ()


def test_writer_line_into_curve_not_g1_raises() -> None:
    w = Writer().start((0, 0)).line((10, 0))
    with pytest.raises(ContinuityError, match="not G1"):
        w.curve((10, 10), (20, 10), (20, 0))


def test_writer_line_into_curve_ok_with_corner() -> None:
    d = (
        Writer()
        .start((0, 0))
        .line((10, 0))
        .corner("knee")
        .curve((10, 10), (20, 10), (20, 0))
        .corner("toe")
        .line((0, 0))
        .close()
        .build()
    )
    assert any(s.kind == "corner" and s.tag == "knee" for s in d.slots)
    assert d.point("knee") == Point(10.0, 0.0)


def test_fragment_start_mismatch_raises() -> None:
    frag = Fragment((LineSegment(Point(5, 5), Point(6, 5)),))
    w = Writer().start((0, 0))
    with pytest.raises(ValueError, match="fragment.start"):
        w.fragment(frag)


def test_counter_role_is_clockwise_and_remaps_node_index() -> None:
    # Draw CCW square; role=counter should reverse to CW and remap indices.
    d = (
        Writer()
        .start((0, 0))
        .node("origin")
        .line((10, 0))
        .line((10, 10))
        .node("far")
        .line((0, 10))
        .close(role="counter")
        .build()
    )
    assert signed_area(d.contours[0]) < 0
    # After reverse, origin (was 0) maps to 0 for closed? (n-0)%n = 0 — stays.
    # far was index 2 on 4-seg contour → (4-2)%4 = 2.
    assert d.point("origin") == Point(0.0, 0.0)
    assert {n.tag: n.index for n in d.nodes[0]}["far"] == 2


def test_duplicate_tag_raises() -> None:
    with pytest.raises(ValueError, match="duplicate tag"):
        (
            Writer()
            .start((0, 0))
            .node("same")
            .line((1, 0))
            .line((1, 1))
            .line((0, 1))
            .node("same")
            .close()
            .build()
        )
