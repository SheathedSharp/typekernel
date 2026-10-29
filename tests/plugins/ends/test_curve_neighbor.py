"""Curve-neighbor EndSite contracts (arc-length point_a/point_b)."""

from __future__ import annotations

import pytest

from tests.plugins.ends.helpers import stem_with_tip_end
from typekernel.draw import apply_slots
from typekernel.draw.slots import EndSite, _seg_length
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment
from typekernel.plugins.ends import angled, ball, flare, flat
from typekernel.system import System

_END_FILLERS = [
    ("flat", flat(inset=0.0)),
    ("flat_inset", flat(inset=0.2)),
    ("angled", angled(deg=12.0)),
    ("ball", ball(radius=6.0)),
    ("flare", flare(amount=0.25, depth=0.2)),
]


@pytest.mark.parametrize("label,filler", _END_FILLERS, ids=[c[0] for c in _END_FILLERS])
def test_end_filler_on_line_cut_still_applies(system: System, label: str, filler) -> None:
    drawing = stem_with_tip_end()
    out = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    assert out.contours[0].closed, label


def test_end_site_point_a_b_along_cubic(system: System) -> None:
    cut = CubicSegment(Point(0, 0), Point(10, -8), Point(30, -8), Point(40, 0))
    site = EndSite(
        tag="tip",
        a=Point(0, 0),
        b=Point(40, 0),
        a_dir=Point(0, 1),
        b_dir=Point(0, 1),
        role="ink",
        cut_edge=cut,
    )
    trim = 5.0
    pa = site.point_a(trim)
    # Linear along chord would stay at y=0; cubic bow pulls y negative.
    assert pa.y < -0.5
    assert _seg_length(cut) > 40.0
    assert site.point_a(0.0).as_tuple() == pytest.approx((0.0, 0.0), abs=1e-6)
    assert site.point_b(0.0).as_tuple() == pytest.approx((40.0, 0.0), abs=1e-6)
    del system
