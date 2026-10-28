"""Contract tests for ``plugins.ends.flat``."""

from __future__ import annotations

from tests.plugins.ends.helpers import contour_area_sign, stem_with_tip_end
from typekernel.draw import apply_slots
from typekernel.geo.segment import LineSegment
from typekernel.plugins.ends import flat
from typekernel.system import System


def test_flat_identity_keeps_topology(system: System) -> None:
    """inset=0 is 槽位与填充协议 noop ≡ unmatched (geometry + tip slot kept)."""
    drawing = stem_with_tip_end()
    before = contour_area_sign(drawing)
    n_before = len(drawing.contours[0].segments)
    unmatched = apply_slots(drawing, system, corners={}, ends={})
    out = apply_slots(drawing, system, corners={}, ends={"tip": flat()})
    assert out.contours[0].closed
    assert contour_area_sign(out) == before
    assert all(isinstance(s, LineSegment) for s in out.contours[0].segments)
    assert len(out.contours[0].segments) == n_before == len(unmatched.contours[0].segments)
    assert {s.tag for s in out.slots if s.kind == "end"} == {"tip"}
    assert {s.tag for s in unmatched.slots if s.kind == "end"} == {"tip"}


def test_flat_with_inset_cap(system: System) -> None:
    drawing = stem_with_tip_end(stem=12.0)
    before = contour_area_sign(drawing)
    out = apply_slots(
        drawing, system, corners={}, ends={"tip": flat(inset=0.2)}
    )
    assert contour_area_sign(out) == before
    assert len(out.contours[0].segments) > 4


def test_flat_deterministic(system: System) -> None:
    drawing = stem_with_tip_end()
    filler = flat(inset=0.1)
    a = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    b = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    assert tuple(type(s).__name__ for s in a.contours[0].segments) == tuple(
        type(s).__name__ for s in b.contours[0].segments
    )
