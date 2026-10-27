"""Contract tests for ``plugins.ends.flare``."""

from __future__ import annotations

from tests.plugins.ends.helpers import contour_area_sign, stem_with_tip_end
from typekernel.draw import apply_slots
from typekernel.plugins.ends import flare
from typekernel.system import System


def test_flare_apply_slots(system: System) -> None:
    drawing = stem_with_tip_end(stem=12.0)
    before = contour_area_sign(drawing)
    out = apply_slots(
        drawing, system, corners={}, ends={"tip": flare(amount=0.35, depth=0.25)}
    )
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    assert len(out.contours[0].segments) > 5
    assert all(s.tag != "tip" for s in out.slots)


def test_flare_deterministic(system: System) -> None:
    drawing = stem_with_tip_end()
    filler = flare()
    a = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    b = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
