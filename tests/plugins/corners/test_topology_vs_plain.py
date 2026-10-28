"""Real serifs must change topology vs plain (ARCHITECTURE.md「槽位与填充协议」)."""

from __future__ import annotations

from tests.plugins.corners.helpers import (
    contour_area_sign,
    segment_kind_sequence,
    square_with_knee,
)
from typekernel.draw import apply_slots
from typekernel.plugins.corners import bracketed, plain, rounded, slab, wedge
from typekernel.system import System


def test_slab_changes_topology_four_to_seven(system: System) -> None:
    """Rectangular slab replaces one corner with a 3-seg bump: 4 → 7 lines."""
    drawing = square_with_knee(meta={"stem": 10.0})
    unmatched = apply_slots(drawing, system, corners={}, ends={})
    with_plain = apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    with_slab = apply_slots(
        drawing,
        system,
        corners={"knee": slab(length=0.42, thickness=0.18)},
        ends={},
    )
    assert len(unmatched.contours[0].segments) == 4
    assert len(with_plain.contours[0].segments) == 4
    assert segment_kind_sequence(with_plain) == segment_kind_sequence(unmatched)
    assert len(with_slab.contours[0].segments) == 7
    assert segment_kind_sequence(with_slab) != segment_kind_sequence(with_plain)
    assert contour_area_sign(with_slab) == contour_area_sign(unmatched)


def test_bracketed_distinct_from_plain_and_slab(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    plain_kinds = segment_kind_sequence(
        apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    )
    slab_kinds = segment_kind_sequence(
        apply_slots(
            drawing,
            system,
            corners={"knee": slab(length=0.42, thickness=0.18)},
            ends={},
        )
    )
    bracketed_kinds = segment_kind_sequence(
        apply_slots(
            drawing,
            system,
            corners={"knee": bracketed(length=0.42, thickness=0.18)},
            ends={},
        )
    )
    assert bracketed_kinds != plain_kinds
    assert bracketed_kinds != slab_kinds
    assert "CubicSegment" in bracketed_kinds
    assert "CubicSegment" not in slab_kinds


def test_rounded_and_wedge_distinct_from_plain(system: System) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    plain_kinds = segment_kind_sequence(
        apply_slots(drawing, system, corners={"knee": plain()}, ends={})
    )
    rounded_kinds = segment_kind_sequence(
        apply_slots(drawing, system, corners={"knee": rounded(radius=0.35)}, ends={})
    )
    wedge_kinds = segment_kind_sequence(
        apply_slots(
            drawing,
            system,
            corners={"knee": wedge(size=0.35)},
            ends={},
        )
    )
    assert rounded_kinds != plain_kinds
    assert wedge_kinds != plain_kinds
