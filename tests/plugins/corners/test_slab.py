"""Contract tests for ``plugins.corners.slab`` (ARCHITECTURE.md §9.5)."""

from __future__ import annotations

import pytest

from tests.plugins.corners.helpers import contour_area_sign, square_with_knee
from typekernel.draw import Writer, apply_slots
from typekernel.geo.segment import LineSegment
from typekernel.plugins.corners import slab
from typekernel.system import System


def test_slab_apply_slots_succeeds(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    before = contour_area_sign(drawing)
    out = apply_slots(
        drawing,
        system,
        corners={"knee": slab(length=0.42, thickness=0.18)},
        ends={},
    )
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    assert all(s.tag != "knee" for s in out.slots)
    # 4 original - 0 + 3 path segs, with trims keeping both edges → more lines
    assert all(isinstance(s, LineSegment) for s in out.contours[0].segments)
    assert len(out.contours[0].segments) >= 5


def test_slab_deterministic(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    filler = slab(length=0.42, thickness=0.18)
    a = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    b = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )


def test_slab_uses_system_stem_when_meta_absent(system: System) -> None:
    # system fixture stem lc=80; length*80=33.6 but edge is only 20 → clamps
    drawing = square_with_knee()
    out = apply_slots(drawing, system, corners={"knee": slab()}, ends={})
    assert out.contours[0].closed


@pytest.mark.parametrize("stem", [6.0, 10.0, 16.0])
def test_slab_over_stem_widths(system: System, stem: float) -> None:
    d = (
        Writer()
        .start((0, 0))
        .line((40, 0))
        .corner("knee", stem=stem)
        .line((40, 40))
        .line((0, 40))
        .close()
        .build()
    )
    before = contour_area_sign(d)
    out = apply_slots(d, system, corners={"knee": slab(length=0.5, thickness=0.25)}, ends={})
    assert contour_area_sign(out) == before
    assert out.contours[0].closed
