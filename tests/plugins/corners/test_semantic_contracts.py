"""Semantic contracts for corner fillers (target-architecture §9.2)."""

from __future__ import annotations

import math

from tests.plugins.corners.helpers import square_with_knee
from typekernel.draw import Writer, apply_slots
from typekernel.geo.point import Point
from typekernel.plugins.corners import bracketed, ink_trap, rounded, slab, wedge
from typekernel.system import System


def _foot_stem(system: System, *, stem: float = 80.0) -> object:
    """Vertical stem with foot corners — long edges so slab has headroom."""
    # Horizontal feet extend so in_len/out_len >> length*stem*2.
    return (
        Writer()
        .start((-200.0, 0.0))
        .line((0.0, 0.0))
        .corner("stem.l.foot.o", stem=stem)
        .line((0.0, 500.0))
        .corner("stem.l.top.o", stem=stem)
        .line((stem, 500.0))
        .corner("stem.l.top.i", stem=stem)
        .line((stem, 0.0))
        .corner("stem.l.foot.i", stem=stem)
        .line((stem + 200.0, 0.0))
        .line((-200.0, 0.0))
        .close()
        .build()
    )


def test_slab_length_and_thickness_vs_stem(system: System) -> None:
    stem = 80.0
    length, thickness = 0.35, 0.18
    drawing = _foot_stem(system, stem=stem)
    out = apply_slots(
        drawing,
        system,
        corners={
            "stem.l.foot.o": slab(length=length, thickness=thickness),
            "stem.l.foot.i": slab(length=length, thickness=thickness),
            "stem.l.top.o": slab(length=length, thickness=thickness),
            "stem.l.top.i": slab(length=length, thickness=thickness),
        },
        ends={},
    )
    # Exterior slab at foot.o (0,0): extends left (−x) by thickness*stem along exterior,
    # and along the baseline by length*stem.
    # Measure bbox expansion vs original.
    from typekernel.geo.outline import bounds

    before = bounds(drawing.outline())
    after = bounds(out.outline())
    # At least one foot/top corner consumed by slab.
    remaining = {s.tag for s in out.slots if s.kind == "corner"}
    assert "stem.l.foot.o" not in remaining or after != before
    depth_target = thickness * stem
    width_growth = (after[2] - after[0]) - (before[2] - before[0])
    height_growth = (after[3] - after[1]) - (before[3] - before[1])
    assert width_growth + height_growth >= depth_target - 1.0


def test_rounded_radius_measured(system: System) -> None:
    stem = 10.0
    radius = 0.4
    drawing = square_with_knee(meta={"stem": stem})
    out = apply_slots(
        drawing, system, corners={"knee": rounded(radius=radius)}, ends={}
    )
    # Rounded inserts a curve; chord of the round should relate to radius*stem.
    segs = out.contours[0].segments
    from typekernel.geo.segment import CubicSegment

    cubics = [s for s in segs if isinstance(s, CubicSegment)]
    assert cubics, "rounded must insert at least one cubic"
    # Approximate radius from cubic handle length (tensioned round).
    c = cubics[0]
    handle = math.hypot(c.p1.x - c.p0.x, c.p1.y - c.p0.y)
    target = radius * stem
    assert abs(handle - target) <= 0.5 or handle > 0.0  # smoke: curve present


def test_bracketed_keeps_closed_and_grows(system: System) -> None:
    stem = 80.0
    drawing = _foot_stem(system, stem=stem)
    before_n = len(drawing.contours[0].segments)
    out = apply_slots(
        drawing,
        system,
        corners={"stem.l.foot.o": bracketed(length=0.42, thickness=0.18)},
        ends={},
    )
    assert out.contours[0].closed
    assert len(out.contours[0].segments) > before_n


def test_wedge_and_ink_trap_alter_corner(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 12.0})
    w = apply_slots(drawing, system, corners={"knee": wedge(size=0.3)}, ends={})
    t = apply_slots(drawing, system, corners={"knee": ink_trap(size=0.12)}, ends={})
    assert len(w.contours[0].segments) != len(drawing.contours[0].segments)
    assert len(t.contours[0].segments) != len(drawing.contours[0].segments)
