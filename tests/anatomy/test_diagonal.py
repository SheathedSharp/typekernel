"""Semantic contracts for diagonal_pair / crossing (target §4.3 / P3-4)."""

from __future__ import annotations

import math

from typekernel.anatomy.diagonal import crossing, diagonal_pair
from typekernel.anatomy.tags import is_valid_tag
from typekernel.geo.contour import signed_area
from typekernel.perceive.topology import measure_topology


def _perp_width(drawing, tag_l: str, tag_r: str) -> float:
    a = drawing.point(tag_l)
    b = drawing.point(tag_r)
    return math.hypot(a.x - b.x, a.y - b.y)


def test_diagonal_pair_perp_thickness_within_half_unit() -> None:
    weight = 80.0
    d = diagonal_pair(
        (200.0, 500.0),
        (60.0, 0.0),
        (340.0, 0.0),
        weight=weight,
        compensate=True,
        thin_ratio=0.85,
    )
    # Top edge of left stroke spans the perpendicular width at the apex end.
    measured = _perp_width(d, "diag.l.top.l", "diag.l.top.r")
    assert abs(measured - weight) <= 0.5
    assert all(is_valid_tag(s.tag) for s in d.slots)
    assert any(m.kind == "crotch" for m in d.measures)


def test_diagonal_pair_with_ink_trap() -> None:
    d = diagonal_pair(
        (200.0, 500.0),
        (80.0, 0.0),
        (320.0, 0.0),
        weight=70.0,
        ink_trap=12.0,
    )
    assert any(n.tag == "diag.vertex" for g in d.nodes for n in g)
    assert len(d.contours) >= 2


def test_crossing_area_cap() -> None:
    weight = 70.0
    d = crossing(
        (40.0, 500.0),
        (360.0, 0.0),
        (360.0, 500.0),
        (40.0, 0.0),
        weight=weight,
        compensate=True,
    )
    measured = _perp_width(d, "cross.a.top.l", "cross.a.top.r")
    assert abs(measured - weight) <= 0.5
    # Raw overlay area sum vs simplified island area — overlap must remove ink.
    raw = sum(abs(signed_area(c)) for c in d.contours)
    topo = measure_topology(d.outline(), stem=weight)
    merged = sum(topo.island_areas) if topo.island_areas else 0.0
    assert topo.islands == 1
    assert merged < raw - 1.0  # real overlap removed
    # Cap: overlap removes at least 5% vs naive sum (no ink blob / double paint).
    single = abs(signed_area(d.contours[0]))
    assert merged <= raw * 0.95
    assert merged < single * 2.0
    assert all(is_valid_tag(s.tag) for s in d.slots)


def test_diagonal_signature_stable() -> None:
    a = diagonal_pair((200, 500), (80, 0), (320, 0), weight=60.0)
    b = diagonal_pair((200, 500), (80, 0), (320, 0), weight=100.0)
    assert a.signature() == b.signature()
