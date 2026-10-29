"""Semantic contracts for stem / crossbar / dot / drop (target §4.3)."""

from __future__ import annotations

import math

import pytest

from typekernel.anatomy.straight import crossbar, dot, drop, stem
from typekernel.anatomy.tags import is_valid_tag
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import bounds


def test_stem_width_slots_and_measure() -> None:
    d = stem(40.0, 120.0, 0.0, 520.0, name="stem.l")
    assert abs((d.point("stem.l.foot.i").x - d.point("stem.l.foot.o").x) - 80.0) < 1e-9
    assert abs((d.point("stem.l.top.i").x - d.point("stem.l.top.o").x) - 80.0) < 1e-9
    corner_tags = sorted(s.tag for s in d.slots if s.kind == "corner")
    assert corner_tags == [
        "stem.l.foot.i",
        "stem.l.foot.o",
        "stem.l.top.i",
        "stem.l.top.o",
    ]
    assert all(is_valid_tag(t) for t in corner_tags)
    assert len(d.measures) == 1
    m = d.measures[0]
    assert m.kind == "stem" and m.expected == 80.0
    assert m.a == "stem.l.foot.o" and m.b == "stem.l.foot.i"
    # CCW ink
    assert signed_area(d.contours[0]) > 0


def test_stem_foot_none_keeps_nodes_without_slots() -> None:
    d = stem(0.0, 50.0, 0.0, 100.0, name="stem", foot="none", top="slot")
    assert d.point("stem.foot.o")
    assert d.point("stem.foot.i")
    kinds = {s.tag: s.kind for s in d.slots}
    assert "stem.foot.o" not in kinds
    assert kinds["stem.top.o"] == "corner"


def test_stem_rejects_non_positive_width() -> None:
    with pytest.raises(ValueError, match="width"):
        stem(100.0, 100.0, 0.0, 100.0, name="stem")


def test_crossbar_thickness_and_end_slots() -> None:
    d = crossbar(50.0, 350.0, 200.0, thick=64.0, name="bar")
    assert abs((d.point("bar.t.l").y - d.point("bar.b.l").y) - 64.0) < 1e-9
    assert abs((d.point("bar.t.r").y - d.point("bar.b.r").y) - 64.0) < 1e-9
    end_tags = sorted(s.tag for s in d.slots if s.kind == "end")
    assert end_tags == ["bar.entry", "bar.exit"]
    assert all(is_valid_tag(t) for t in end_tags)
    assert all(is_valid_tag(s.tag) for s in d.slots)
    assert d.measures[0].expected == 64.0


def test_crossbar_ends_none() -> None:
    d = crossbar(0.0, 200.0, 100.0, thick=40.0, name="bar", ends="none")
    assert not any(s.kind == "end" for s in d.slots)
    assert len([s for s in d.slots if s.kind == "corner"]) == 4


def test_dot_round_bounds_and_square() -> None:
    round_d = dot((100.0, 100.0), 50.0, shape="round", overshoot=0.0)
    bx = bounds(round_d.outline())
    assert abs((bx[2] - bx[0]) - 50.0) < 0.5
    assert abs((bx[3] - bx[1]) - 50.0) < 0.5
    assert is_valid_tag("dot.stress")
    assert round_d.measures[0].kind == "height"

    sq = dot((0.0, 0.0), 40.0, shape="square")
    bx2 = bounds(sq.outline())
    assert abs((bx2[2] - bx2[0]) - 40.0) < 1e-9
    assert abs((bx2[3] - bx2[1]) - 40.0) < 1e-9
    assert all(is_valid_tag(s.tag) for s in sq.slots)


def test_drop_single_contour_end_slot_and_width() -> None:
    d = drop((0.0, 80.0), (0.0, 0.0), width=36.0, tail_curve=0.55)
    assert len(d.contours) == 1
    assert d.contours[0].closed
    end_tags = [s.tag for s in d.slots if s.kind == "end"]
    assert end_tags == ["drop.exit"]
    assert all(is_valid_tag(s.tag) for s in d.slots)
    # Head width: distance between entry and stress nodes ≈ width
    a = d.point("drop.entry")
    b = d.point("drop.stress")
    assert abs(math.hypot(a.x - b.x, a.y - b.y) - 36.0) < 1e-6


def test_stem_signature_stable_across_width() -> None:
    a = stem(0.0, 70.0, 0.0, 500.0, name="stem.l")
    b = stem(0.0, 110.0, 0.0, 500.0, name="stem.l")
    assert a.signature() == b.signature()
