"""Degenerate corner parameters must follow the plain/unmatched noop path (§9.5)."""

from __future__ import annotations

import pytest

from tests.plugins.corners.helpers import (
    corner_slot_tags,
    line_curve_knee,
    segment_kind_sequence,
    square_with_knee,
)
from typekernel.draw import apply_slots
from typekernel.plugins.corners import bracketed, ink_trap, rounded, slab, wedge
from typekernel.system import System


def _unmatched(drawing, system: System):
    return apply_slots(drawing, system, corners={}, ends={})


@pytest.mark.parametrize(
    "make_filler",
    [
        lambda: rounded(radius=0.0),
        lambda: slab(length=0.0, thickness=0.0),
        lambda: wedge(size=0.0),
        lambda: bracketed(length=0.0, thickness=0.0),
        lambda: ink_trap(size=0.0),
    ],
    ids=["rounded0", "slab0", "wedge0", "bracketed0", "ink_trap0"],
)
@pytest.mark.parametrize(
    "fixture", [square_with_knee, line_curve_knee], ids=["line_line", "line_curve"]
)
def test_degenerate_corner_fill_does_not_increase_segment_count(
    system: System, make_filler, fixture
) -> None:
    """radius/size/length→0 must not add segments (noop ≡ unmatched)."""
    drawing = fixture()
    unmatched = _unmatched(drawing, system)
    out = apply_slots(drawing, system, corners={"knee": make_filler()}, ends={})
    assert len(out.contours[0].segments) == len(unmatched.contours[0].segments)
    assert segment_kind_sequence(out) == segment_kind_sequence(unmatched)
    assert corner_slot_tags(out) == corner_slot_tags(unmatched)
    assert "knee" in corner_slot_tags(out)



@pytest.mark.parametrize(
    "make_filler",
    [
        lambda: rounded(radius=0.0),
        lambda: slab(length=0.0, thickness=0.0),
        lambda: wedge(size=0.0),
        lambda: bracketed(length=0.0, thickness=0.0),
        lambda: ink_trap(size=0.0),
    ],
    ids=["rounded0", "slab0", "wedge0", "bracketed0", "ink_trap0"],
)
def test_degenerate_fill_returns_path_none(system: System, make_filler) -> None:
    from typekernel.draw.slots import CornerSite
    from typekernel.geo.point import Point

    site = CornerSite(
        tag="knee",
        point=Point(20.0, 0.0),
        in_dir=Point(1.0, 0.0),
        out_dir=Point(0.0, 1.0),
        in_len=20.0,
        out_len=20.0,
        role="ink",
    )
    fill = make_filler()(site, system)
    assert fill.trim_in == 0.0 and fill.trim_out == 0.0
    assert fill.path is None
