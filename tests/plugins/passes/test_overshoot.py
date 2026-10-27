"""Contract tests for ``plugins.passes.overshoot``."""

from __future__ import annotations

from tests.plugins.passes.helpers import make_system, round_rect_at_x_height
from typekernel.plugins.passes import overshoot


def test_overshoot_shifts_top_near_x_height() -> None:
    system = make_system(round_os=12.0)
    d = round_rect_at_x_height(x=500.0)
    out = overshoot(d, system, kind="round")
    # Top edge was y=500; should move to 512.
    ys = []
    for seg in out.contours[0].segments:
        ys.append(seg.p0.y)
        if hasattr(seg, "p1"):
            ys.append(seg.p1.y)
    assert max(ys) == 512.0
    assert out.nodes == d.nodes
    assert out.slots == d.slots


def test_overshoot_at_tag_only() -> None:
    system = make_system(round_os=12.0)
    d = round_rect_at_x_height(x=500.0)
    out = overshoot(d, system, kind="round", at="top")
    # Node "top" is at index of (half, x) start of next segment — check a point moved.
    # Without full scan: ymax should still rise because top nodes are on y=500.
    ys = [seg.p0.y for seg in out.contours[0].segments] + [
        seg.p1.y for seg in out.contours[0].segments
    ]
    assert max(ys) >= 512.0 - 1e-9


def test_overshoot_pointed_amount() -> None:
    system = make_system(round_os=12.0, pointed_os=10.0)
    d = round_rect_at_x_height(x=500.0)
    out = overshoot(d, system, kind="pointed")
    ys = [seg.p0.y for seg in out.contours[0].segments] + [
        seg.p1.y for seg in out.contours[0].segments
    ]
    assert max(ys) == 510.0


def test_overshoot_deterministic() -> None:
    system = make_system()
    d = round_rect_at_x_height()
    a = overshoot(d, system)
    b = overshoot(d, system)
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
