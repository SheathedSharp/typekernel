"""apply_slots with fake fillers (§9.9)."""

from __future__ import annotations

import pytest

from typekernel.draw import (
    CornerFill,
    CornerSite,
    Fragment,
    SlotFillError,
    Writer,
    apply_slots,
)
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.system import System


def _square_with_corner() -> object:
    return (
        Writer()
        .start((0, 0))
        .line((20, 0))
        .corner("knee")
        .line((20, 20))
        .line((0, 20))
        .close()
        .build()
    )


def _chamfer(site: CornerSite, system: System) -> CornerFill:
    trim = 2.0
    # Back along -in_dir from point, forward along out_dir
    a = Point(
        site.point.x - site.in_dir.x * trim,
        site.point.y - site.in_dir.y * trim,
    )
    b = Point(
        site.point.x + site.out_dir.x * trim,
        site.point.y + site.out_dir.y * trim,
    )
    path = Fragment((LineSegment(a, b),))
    return CornerFill(trim_in=trim, trim_out=trim, path=path)


def test_apply_slots_replaces_matched_corner_and_stays_continuous() -> None:
    drawing = _square_with_corner()
    system = System()
    out = apply_slots(drawing, system, corners={"knee": _chamfer}, ends={})
    assert all(s.tag != "knee" for s in out.slots)
    # Corner cut: more than 4 segments (chamfer adds an edge, removes the sharp corner)
    assert len(out.contours[0].segments) == 5
    # Unfilled would be 4; chamfer keeps continuity (line-line joins ok)


def test_unmatched_slot_preserved() -> None:
    drawing = _square_with_corner()
    out = apply_slots(drawing, System(), corners={"other*": _chamfer}, ends={})
    assert any(s.tag == "knee" for s in out.slots)
    assert len(out.contours[0].segments) == 4


def test_trim_out_of_range_raises() -> None:
    drawing = _square_with_corner()

    def too_much(site: CornerSite, system: System) -> CornerFill:
        trim = site.in_len + 10.0
        a = Point(site.point.x - site.in_dir.x * 1.0, site.point.y - site.in_dir.y * 1.0)
        b = Point(site.point.x + site.out_dir.x * 1.0, site.point.y + site.out_dir.y * 1.0)
        return CornerFill(trim_in=trim, trim_out=1.0, path=Fragment((LineSegment(a, b),)))

    with pytest.raises(SlotFillError, match="trim exceeds"):
        apply_slots(drawing, System(), corners={"knee": too_much}, ends={})
