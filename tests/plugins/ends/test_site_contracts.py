"""Synthetic EndSite contracts for every end filler (ARCHITECTURE 槽位与填充协议)."""

from __future__ import annotations

import pytest

from tests.plugins.ends.helpers import (
    contour_area_sign,
    end_slot_tags,
    make_system,
    segment_kind_sequence,
    stem_with_tip_end,
)
from typekernel.draw import apply_slots
from typekernel.plugins.ends import angled, ball, flare, flat
from typekernel.system import System

_END_CASES = [
    ("flat0", flat(inset=0.0), False),
    ("flat", flat(inset=0.2), True),
    ("angled", angled(deg=12.0), True),
    ("ball", ball(radius=6.0), True),
    ("flare", flare(amount=0.35, depth=0.25), True),
]


@pytest.mark.parametrize(
    "label,filler,alters",
    _END_CASES,
    ids=[c[0] for c in _END_CASES],
)
def test_end_filler_legal_topology(
    system: System, label: str, filler, alters: bool
) -> None:
    drawing = stem_with_tip_end(stem=12.0)
    before_sign = contour_area_sign(drawing)
    before_n = len(drawing.contours[0].segments)
    out = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    assert out.contours[0].closed, label
    assert contour_area_sign(out) == before_sign, label
    if alters:
        assert len(out.contours[0].segments) != before_n, label
        assert "tip" not in end_slot_tags(out), label
    else:
        assert len(out.contours[0].segments) == before_n, label
        assert "tip" in end_slot_tags(out), label


@pytest.mark.parametrize(
    "label,filler",
    [(c[0], c[1]) for c in _END_CASES],
    ids=[c[0] for c in _END_CASES],
)
def test_end_filler_cross_master_kind_stable(label: str, filler) -> None:
    light = make_system(stem=60.0)
    bold = make_system(stem=120.0)
    drawing = stem_with_tip_end(stem=12.0)
    a = apply_slots(drawing, light, corners={}, ends={"tip": filler})
    b = apply_slots(drawing, bold, corners={}, ends={"tip": filler})
    assert segment_kind_sequence(a) == segment_kind_sequence(b), label


@pytest.mark.parametrize("stem", [8.0, 12.0, 20.0])
@pytest.mark.parametrize(
    "label,filler",
    [
        ("angled", angled(deg=10.0)),
        ("flare", flare(amount=0.3, depth=0.2)),
        ("flat", flat(inset=0.15)),
    ],
)
def test_end_filler_over_stem_widths(system: System, stem: float, label: str, filler) -> None:
    drawing = stem_with_tip_end(stem=stem)
    before = contour_area_sign(drawing)
    out = apply_slots(drawing, system, corners={}, ends={"tip": filler})
    assert out.contours[0].closed, label
    assert contour_area_sign(out) == before, label
