"""Degenerate end parameters must follow the unmatched noop path (槽位与填充协议)."""

from __future__ import annotations

import pytest

from tests.plugins.ends.helpers import (
    end_slot_tags,
    segment_kind_sequence,
    stem_with_tip_end,
)
from typekernel.draw import apply_slots
from typekernel.draw.geomutil import segment_end, segment_start
from typekernel.plugins.ends import angled, ball, flare, flat
from typekernel.system import System


def _unmatched(drawing, system: System):
    return apply_slots(drawing, system, corners={}, ends={})


@pytest.mark.parametrize(
    "make_filler",
    [
        lambda: flat(inset=0.0),
        lambda: ball(radius=0.0),
        lambda: flare(amount=0.0, depth=0.0),
        lambda: angled(deg=0.0),
    ],
    ids=["flat0", "ball0", "flare0", "angled0"],
)
def test_degenerate_end_fill_matches_unmatched(system: System, make_filler) -> None:
    """inset/radius/amount/deg → 0 must not add segments and must keep the end slot."""
    drawing = stem_with_tip_end()
    unmatched = _unmatched(drawing, system)
    out = apply_slots(drawing, system, corners={}, ends={"tip": make_filler()})
    assert len(out.contours[0].segments) == len(unmatched.contours[0].segments)
    assert segment_kind_sequence(out) == segment_kind_sequence(unmatched)
    assert end_slot_tags(out) == end_slot_tags(unmatched) == {"tip"}
    for a, b in zip(out.contours[0].segments, unmatched.contours[0].segments, strict=True):
        assert segment_start(a) == segment_start(b)
        assert segment_end(a) == segment_end(b)


@pytest.mark.parametrize(
    "make_filler",
    [
        lambda: flat(inset=0.0),
        lambda: ball(radius=0.0),
        lambda: flare(amount=0.0, depth=0.0),
        lambda: angled(deg=0.0),
    ],
    ids=["flat0", "ball0", "flare0", "angled0"],
)
def test_degenerate_end_fill_returns_path_none(system: System, make_filler) -> None:
    from typekernel.draw.slots import EndSite
    from typekernel.geo.point import Point

    site = EndSite(
        tag="tip",
        a=Point(-5.0, 40.0),
        b=Point(5.0, 40.0),
        a_dir=Point(0.0, 1.0),
        b_dir=Point(0.0, 1.0),
        role="ink",
    )
    fill = make_filler()(site, system)
    assert fill.trim_a == 0.0 and fill.trim_b == 0.0
    assert fill.path is None
