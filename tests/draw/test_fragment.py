"""Fragment / Node tests (ARCHITECTURE.md 测试清单 — synthetic shapes only)."""

from __future__ import annotations

import math

import pytest

from typekernel.draw import ContinuityError, Fragment, Node
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment


def _line(a: tuple[float, float], b: tuple[float, float]) -> LineSegment:
    return LineSegment(Point(*a), Point(*b))


def _cubic(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
) -> CubicSegment:
    return CubicSegment(Point(*p0), Point(*p1), Point(*p2), Point(*p3))


def test_fragment_rejects_disjoint_chain() -> None:
    with pytest.raises(ValueError, match="do not chain"):
        Fragment((_line((0, 0), (10, 0)), _line((11, 0), (20, 0))))


def test_fragment_curve_join_not_g1_raises_continuity_error() -> None:
    # Horizontal line into a cubic whose outgoing handle is vertical → not G1.
    prev = _line((0, 0), (10, 0))
    nxt = _cubic((10, 0), (10, 10), (20, 10), (20, 0))
    with pytest.raises(ContinuityError, match="not G1"):
        Fragment((prev, nxt))


def test_fragment_curve_join_allowed_with_cusp_meta() -> None:
    prev = _line((0, 0), (10, 0))
    nxt = _cubic((10, 0), (10, 10), (20, 10), (20, 0))
    frag = Fragment(
        (prev, nxt),
        nodes=(Node(index=1, tag="kink", meta={"cusp": 1.0}),),
    )
    assert frag.start == Point(0.0, 0.0)
    assert frag.end == Point(20.0, 0.0)


def test_fragment_line_line_corner_ok_without_declaration() -> None:
    frag = Fragment((_line((0, 0), (10, 0)), _line((10, 0), (10, 10))))
    assert len(frag.segments) == 2


def test_reversed_remaps_node_indices_and_geometry() -> None:
    frag = Fragment(
        (_line((0, 0), (10, 0)), _line((10, 0), (10, 20))),
        nodes=(Node(0, "start"), Node(2, "end")),
    )
    rev = frag.reversed()
    assert rev.start == Point(10.0, 20.0)
    assert rev.end == Point(0.0, 0.0)
    tags = {n.tag: n.index for n in rev.nodes}
    assert tags == {"start": 2, "end": 0}


def test_mirrored_x_geometry_and_node_index_remap() -> None:
    frag = Fragment(
        (_line((0, 0), (10, 0)), _line((10, 0), (10, 5))),
        nodes=(Node(0, "origin"), Node(1, "knee"), Node(2, "tip")),
    )
    mirrored = frag.mirrored_x(0.0)
    # Mirror then reverse: start is former end mirrored.
    assert mirrored.start == Point(-10.0, 5.0)
    assert mirrored.end == Point(0.0, 0.0)
    by_tag = {n.tag: n.index for n in mirrored.nodes}
    assert by_tag["origin"] == 2
    assert by_tag["tip"] == 0
    assert by_tag["knee"] == 1


def test_translated_and_tagged() -> None:
    frag = Fragment(
        (_line((0, 0), (1, 0)),),
        nodes=(Node(0, "point"),),
    )
    moved = frag.translated(3.0, -2.0).tagged("stem")
    assert moved.start == Point(3.0, -2.0)
    assert moved.nodes[0].tag == "stem.point"


def test_start_end_tangents_are_unit() -> None:
    frag = Fragment((_line((0, 0), (3, 4)),))
    st = frag.start_tangent()
    et = frag.end_tangent()
    assert math.isclose(math.hypot(st.x, st.y), 1.0, abs_tol=1e-9)
    assert math.isclose(math.hypot(et.x, et.y), 1.0, abs_tol=1e-9)
    assert st == Point(0.6, 0.8)
    assert et == Point(0.6, 0.8)
