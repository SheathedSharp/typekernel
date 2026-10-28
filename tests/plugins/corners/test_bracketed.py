"""Contract tests for ``plugins.corners.bracketed`` (ARCHITECTURE.md 槽位与填充协议)."""

from __future__ import annotations

from tests.plugins.corners.helpers import contour_area_sign, square_with_knee
from typekernel.draw import apply_slots
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.plugins.corners import bracketed
from typekernel.system import System


def test_bracketed_apply_slots_has_cubic_bracket(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    before = contour_area_sign(drawing)
    out = apply_slots(
        drawing,
        system,
        corners={"knee": bracketed(length=0.42, thickness=0.18)},
        ends={},
    )
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    segs = out.contours[0].segments
    assert any(isinstance(s, LineSegment) for s in segs)
    assert any(isinstance(s, CubicSegment) for s in segs)
    assert all(s.tag != "knee" for s in out.slots)


def test_bracketed_deterministic(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    filler = bracketed()
    a = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    b = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )


def test_bracketed_preserves_winding_on_large_square(system: System) -> None:
    from typekernel.draw import Writer

    d = (
        Writer()
        .start((0, 0))
        .line((50, 0))
        .corner("knee", stem=12.0)
        .line((50, 50))
        .line((0, 50))
        .close()
        .build()
    )
    before = contour_area_sign(d)
    out = apply_slots(d, system, corners={"knee": bracketed(length=0.5, thickness=0.2)}, ends={})
    assert contour_area_sign(out) == before
