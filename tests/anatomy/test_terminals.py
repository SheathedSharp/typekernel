"""Semantic contracts for hook / tail / ear / spur (target §4.3 / P3-5)."""

from __future__ import annotations

from typekernel.anatomy.tags import is_valid_tag
from typekernel.anatomy.terminals import ear, hook, spur, tail


def test_hook_has_thickness_and_end_slot() -> None:
    d = hook(
        100.0,
        200.0,
        tip=(40.0, 80.0),
        thick=70.0,
        thin=50.0,
        depth=30.0,
        tension=0.55,
    )
    ends = [s.tag for s in d.slots if s.kind == "end"]
    assert ends == ["hook.exit"]
    assert all(is_valid_tag(s.tag) for s in d.slots)
    assert any(m.kind == "stem" and m.expected == 70.0 for m in d.measures)
    light = hook(100.0, 200.0, tip=(40.0, 80.0), thick=50.0, thin=35.0, depth=30.0)
    bold = hook(100.0, 200.0, tip=(40.0, 80.0), thick=90.0, thin=60.0, depth=30.0)
    assert light.signature() == bold.signature()


def test_tail_and_ear_end_slots() -> None:
    t = tail((200.0, 200.0), (260.0, 40.0), thick=60.0, thin=28.0)
    assert [s.tag for s in t.slots if s.kind == "end"] == ["tail.exit"]
    assert all(is_valid_tag(s.tag) for s in t.slots)
    e = ear((200.0, 400.0), (250.0, 460.0), thick=36.0)
    assert any(s.kind == "end" for s in e.slots)


def test_spur_end_slot_and_thickness() -> None:
    d = spur(120.0, 300.0, length=45.0, thick=48.0, side="right")
    assert any(s.kind == "end" and s.tag == "spur.exit" for s in d.slots)
    assert all(is_valid_tag(s.tag) for s in d.slots)
    assert d.point("spur.entry") is not None
    from typekernel.geo.outline import bounds

    bx = bounds(d.outline())
    assert abs((bx[3] - bx[1]) - 48.0) < 1e-9
