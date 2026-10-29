"""Semantic contracts for arch / bowl / open_bowl / spine (target §4.3 / P3-3)."""

from __future__ import annotations

from typekernel.anatomy.curves import BarSpec, arch, bowl, bowl_join, open_bowl, spine
from typekernel.anatomy.tags import is_valid_tag
from typekernel.geo.outline import bounds
from typekernel.optics.stem import measure_horizontal_stem, measure_vertical_stem
from typekernel.perceive.topology import measure_topology


def test_arch_join_depth_crown_and_thin() -> None:
    d = arch(
        100.0,
        400.0,
        height=520.0,
        thick=70.0,
        thin=55.0,
        join_depth=40.0,
        tension=0.55,
        overshoot=12.0,
        crown_shift=8.0,
    )
    join = d.point("arch.crotch.l")
    entry = d.point("arch.entry")
    assert abs(join.y - (520.0 - 40.0)) < 1e-9
    assert abs(abs(join.y - entry.y) - 55.0) < 1.0  # thin ± 1
    bx = bounds(d.outline())
    assert 520.0 - 1e-6 <= bx[3] <= 520.0 + 12.0 + 1e-6
    assert all(is_valid_tag(s.tag) for s in d.slots)
    # Signature stable across weight-like param change
    light = arch(
        100.0, 400.0, height=520.0, thick=50.0, thin=40.0, join_depth=40.0, tension=0.55
    )
    bold = arch(
        100.0, 400.0, height=520.0, thick=90.0, thin=70.0, join_depth=40.0, tension=0.55
    )
    assert light.signature() == bold.signature()


def test_bowl_horizontal_and_vertical_thickness() -> None:
    d = bowl((200.0, 260.0), 180.0, 260.0, thick=84.0, thin=70.0, overshoot=12.0)
    ol = d.outline()
    v = measure_vertical_stem(ol, 60.0)
    assert v is not None and abs(v - 84.0) < 1.0
    outer_ry = 260.0 + 12.0
    y_top = 260.0 + outer_ry - 70.0 / 2.0
    h = measure_horizontal_stem(ol, y_top)
    assert h is not None and abs(h - 70.0) < 1.0
    light = bowl((200.0, 260.0), 180.0, 260.0, thick=60.0, thin=50.0)
    bold = bowl((200.0, 260.0), 180.0, 260.0, thick=100.0, thin=80.0)
    assert light.signature() == bold.signature()


def test_bowl_stress_angle_recorded() -> None:
    d = bowl(
        (0.0, 0.0), 100.0, 120.0, thick=30.0, thin=20.0, stress_deg=15.0
    )
    assert any(
        m.direction_deg is not None and abs(m.direction_deg - 15.0) < 1e-9
        for m in d.measures
        if m.kind == "stem"
    )


def test_open_bowl_terminals_are_end_slots() -> None:
    d = open_bowl(
        (200.0, 260.0), 180.0, 260.0, thick=84.0, thin=70.0, aperture=0.42
    )
    ends = sorted(s.tag for s in d.slots if s.kind == "end")
    assert ends == ["aperture.0.a", "aperture.0.b"]
    assert all(is_valid_tag(t) for t in ends)
    topo = measure_topology(d.outline(), stem=84.0)
    assert topo.islands == 1
    assert topo.counters == 0  # open C


def test_open_bowl_with_bar_one_counter_one_aperture() -> None:
    d = open_bowl(
        (200.0, 260.0),
        180.0,
        260.0,
        thick=84.0,
        thin=70.0,
        aperture=0.42,
        bar=BarSpec(y=180.0, thick=70.0, inset=8.0),
    )
    topo = measure_topology(d.outline(), stem=84.0)
    assert topo.islands == 1
    assert topo.counters == 1
    assert topo.slit_counters == 0
    light = open_bowl(
        (200.0, 260.0), 180.0, 260.0, thick=60.0, thin=50.0, aperture=0.42
    )
    bold = open_bowl(
        (200.0, 260.0), 180.0, 260.0, thick=100.0, thin=80.0, aperture=0.42
    )
    assert light.signature() == bold.signature()


def test_bowl_join_has_crotch_measure_and_no_slit() -> None:
    d = bowl_join(
        40.0,
        (220.0, 260.0),
        160.0,
        220.0,
        side="left",
        thick=84.0,
        thin=70.0,
        crotch=50.0,
    )
    assert any(m.kind == "crotch" and m.expected == 50.0 for m in d.measures)
    topo = measure_topology(d.outline(), stem=84.0)
    assert topo.slit_counters == 0
    assert topo.islands == 1


def test_spine_end_slots_and_signature_stable() -> None:
    d = spine((200.0, 500.0), (200.0, 0.0), thick=80.0, thin=50.0, tension=0.55)
    ends = sorted(s.tag for s in d.slots if s.kind == "end")
    assert ends == ["spine.entry", "spine.exit"]
    assert all(is_valid_tag(t) for t in ends)
    other = spine((200.0, 500.0), (200.0, 0.0), thick=100.0, thin=40.0, tension=0.55)
    assert d.signature() == other.signature()


def test_open_bowl_survives_plain_apply_slots() -> None:
    """Unmatched end slots + inner corners stay exempt after plain fill."""
    from typekernel.draw import apply_slots
    from typekernel.plugins.corners import plain
    from typekernel.starters.latin_sans.system import system

    d = open_bowl(
        (200.0, 260.0), 180.0, 260.0, thick=84.0, thin=70.0, aperture=0.42
    )
    out = apply_slots(d, system, corners={"*": plain()}, ends={})
    ends = sorted(s.tag for s in out.slots if s.kind == "end")
    assert ends == ["aperture.0.a", "aperture.0.b"]
    topo = measure_topology(out.outline(), stem=84.0)
    assert topo.islands == 1
    assert topo.counters == 0
