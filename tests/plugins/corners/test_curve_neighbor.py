"""Curve-neighbor CornerSite contracts (arc-length trim + requires skip)."""

from __future__ import annotations

import pytest

from tests.plugins.corners.helpers import (
    line_curve_knee,
    segment_kind_sequence,
    square_with_knee,
)
from typekernel.draw import apply_slots
from typekernel.draw.slots import _corner_site_from_segs
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.plugins.corners import bracketed, ink_trap, plain, rounded, slab, wedge
from typekernel.system import System

_REQUIRES_LINE = [
    ("rounded", rounded(radius=4.0)),
    ("slab", slab(length=0.42, thickness=0.18)),
    ("bracketed", bracketed(length=0.42, thickness=0.18)),
    ("wedge", wedge(size=0.3)),
    ("ink_trap", ink_trap(size=0.12, curved=False)),
]


@pytest.mark.parametrize("label,filler", _REQUIRES_LINE, ids=[c[0] for c in _REQUIRES_LINE])
def test_curve_neighbor_skipped_when_requires_line_line(
    system: System, label: str, filler
) -> None:
    """Fillers that need straight edges skip curve neighbors without error."""
    drawing = line_curve_knee(meta={"stem": 10.0})
    before = segment_kind_sequence(drawing)
    out = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    # Knee left unmatched (still declared); geometry of knee join unchanged.
    assert "knee" in {s.tag for s in out.slots if s.kind == "corner"}, label
    assert segment_kind_sequence(out) == before, label


@pytest.mark.parametrize("label,filler", _REQUIRES_LINE, ids=[c[0] for c in _REQUIRES_LINE])
def test_line_line_neighbor_still_fills(system: System, label: str, filler) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    out = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    assert all(s.tag != "knee" for s in out.slots), label
    assert segment_kind_sequence(out) != segment_kind_sequence(drawing), label


def test_plain_on_curve_neighbor_is_noop(system: System) -> None:
    drawing = line_curve_knee()
    out = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    assert segment_kind_sequence(out) == segment_kind_sequence(drawing)
    assert "knee" in {s.tag for s in out.slots if s.kind == "corner"}


def test_point_in_out_follow_curved_edge(system: System) -> None:
    """On a bowed cubic, arc-length point_out differs from tangent*trim."""
    # Incoming line to (0,0); outgoing cubic bows upward while leaving along +x.
    segs = [
        LineSegment(Point(-40, 0), Point(0, 0)),
        CubicSegment(Point(0, 0), Point(20, 0), Point(40, 30), Point(60, 30)),
        LineSegment(Point(60, 30), Point(60, -10)),
        LineSegment(Point(60, -10), Point(-40, -10)),
        LineSegment(Point(-40, -10), Point(-40, 0)),
    ]
    site = _corner_site_from_segs(
        segs, 1, tag="knee", role="ink", meta={"stem": 10.0}
    )
    assert isinstance(site.out_edge, CubicSegment)
    trim = 25.0
    b = site.point_out(trim)
    linear = Point(
        site.point.x + site.out_dir.x * trim,
        site.point.y + site.out_dir.y * trim,
    )
    assert abs(b.x - linear.x) + abs(b.y - linear.y) > 1.0
    # point_in along a straight edge matches the linear fallback.
    a = site.point_in(10.0)
    assert abs(a.x - (site.point.x - site.in_dir.x * 10.0)) < 1e-6
    assert abs(a.y - (site.point.y - site.in_dir.y * 10.0)) < 1e-6
    del system
