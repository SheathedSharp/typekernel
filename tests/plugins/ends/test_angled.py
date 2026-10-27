"""Contract tests for ``plugins.ends.angled``."""

from __future__ import annotations

from tests.plugins.ends.helpers import contour_area_sign, stem_with_tip_end
from typekernel.draw import apply_slots
from typekernel.plugins.ends import angled
from typekernel.system import System


def test_angled_apply_slots(system: System) -> None:
    drawing = stem_with_tip_end()
    before = contour_area_sign(drawing)
    out = apply_slots(drawing, system, corners={}, ends={"tip": angled(deg=12)})
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    assert all(s.tag != "tip" for s in out.slots)
    assert len(out.contours[0].segments) > 4


def test_angled_deterministic(system: System) -> None:
    drawing = stem_with_tip_end()
    filler = angled(deg=18)
    a = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    b = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
