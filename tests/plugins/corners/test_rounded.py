"""Contract tests for ``plugins.corners.rounded`` (ARCHITECTURE.md §9.5)."""

from __future__ import annotations

import pytest

from tests.plugins.corners.helpers import contour_area_sign, square_with_knee
from typekernel.draw import Writer, apply_slots
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.plugins.corners import rounded
from typekernel.system import System


def test_rounded_apply_slots_fillets_corner(system: System) -> None:
    drawing = square_with_knee()
    before_sign = contour_area_sign(drawing)
    out = apply_slots(
        drawing, system, corners={"knee": rounded(radius=4.0)}, ends={}
    )
    assert out.contours[0].closed
    assert contour_area_sign(out) == before_sign
    segs = out.contours[0].segments
    assert any(isinstance(s, CubicSegment) for s in segs)
    assert all(s.tag != "knee" for s in out.slots)


def test_rounded_deterministic_kinds(system: System) -> None:
    drawing = square_with_knee()
    filler = rounded(radius=3.0)
    a = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    b = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )


def test_rounded_default_radius_from_stem(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    out = apply_slots(drawing, system, corners={"knee": rounded()}, ends={})
    # Default radius = 0.5 * stem = 5, clamped to half of edge (10) → 5
    cubics = [s for s in out.contours[0].segments if isinstance(s, CubicSegment)]
    assert len(cubics) == 1


def test_rounded_clamps_to_edge(system: System) -> None:
    drawing = square_with_knee()
    out = apply_slots(
        drawing, system, corners={"knee": rounded(radius=1000.0)}, ends={}
    )
    assert out.contours[0].closed
    assert any(isinstance(s, CubicSegment) for s in out.contours[0].segments)


@pytest.mark.parametrize("angle_deg", [60.0, 90.0, 120.0])
def test_rounded_over_angles(system: System, angle_deg: float) -> None:
    import math

    rad = math.radians(angle_deg)
    # Polyline: horizontal into corner, then leave at `angle_deg` turn (left).
    # Exterior corner of a wedge shape.
    x1, y1 = 30.0, 0.0
    x2 = 30.0 + 30.0 * math.cos(rad)
    y2 = 0.0 + 30.0 * math.sin(rad)
    d = (
        Writer()
        .start((0, 0))
        .line((x1, y1))
        .corner("knee")
        .line((x2, y2))
        .line((0, 40))
        .close()
        .build()
    )
    before = contour_area_sign(d)
    out = apply_slots(d, system, corners={"knee": rounded(radius=5.0)}, ends={})
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    assert any(isinstance(s, (CubicSegment, LineSegment)) for s in out.contours[0].segments)


def test_rounded_zero_radius_is_sharp(system: System) -> None:
    drawing = square_with_knee()
    out = apply_slots(drawing, system, corners={"knee": rounded(radius=0.0)}, ends={})
    assert all(isinstance(s, LineSegment) for s in out.contours[0].segments)
