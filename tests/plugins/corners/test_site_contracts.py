"""Synthetic CornerSite contracts for every corner filler (ARCHITECTURE §9.5)."""

from __future__ import annotations

import pytest

from tests.plugins.corners.helpers import (
    contour_area_sign,
    make_system,
    segment_kind_sequence,
    square_with_knee,
)
from typekernel.draw import apply_slots
from typekernel.plugins.corners import bracketed, ink_trap, plain, rounded, slab, wedge
from typekernel.system import System

# Non-degenerate factories: must alter topology (except plain).
_CORNER_CASES = [
    ("plain", plain(), False),
    ("rounded", rounded(radius=0.35), True),
    ("slab", slab(length=0.42, thickness=0.18), True),
    ("bracketed", bracketed(length=0.42, thickness=0.18), True),
    ("wedge", wedge(size=0.3), True),
    ("ink_trap", ink_trap(size=0.12, curved=True), True),
]


@pytest.mark.parametrize(
    "label,filler,alters",
    _CORNER_CASES,
    ids=[c[0] for c in _CORNER_CASES],
)
def test_corner_filler_legal_topology(
    system: System, label: str, filler, alters: bool
) -> None:
    drawing = square_with_knee(meta={"stem": 10.0})
    before_sign = contour_area_sign(drawing)
    before_n = len(drawing.contours[0].segments)
    out = apply_slots(drawing, system, corners={"knee": filler}, ends={})
    assert out.contours[0].closed, label
    assert contour_area_sign(out) == before_sign, label
    assert len(out.contours[0].segments) >= 1, label
    if alters:
        assert len(out.contours[0].segments) != before_n, label
        assert all(s.tag != "knee" for s in out.slots), label
    else:
        assert len(out.contours[0].segments) == before_n, label
        assert "knee" in {s.tag for s in out.slots if s.kind == "corner"}, label


@pytest.mark.parametrize(
    "label,filler",
    [(c[0], c[1]) for c in _CORNER_CASES],
    ids=[c[0] for c in _CORNER_CASES],
)
def test_corner_filler_cross_master_kind_stable(label: str, filler) -> None:
    """Same filler + two stem Systems → identical segment kind sequences."""
    light = make_system(stem=60.0)
    bold = make_system(stem=120.0)
    drawing = square_with_knee(meta={"stem": 10.0})
    a = apply_slots(drawing, light, corners={"knee": filler}, ends={})
    b = apply_slots(drawing, bold, corners={"knee": filler}, ends={})
    assert segment_kind_sequence(a) == segment_kind_sequence(b), label


@pytest.mark.parametrize("stem", [6.0, 10.0, 18.0])
@pytest.mark.parametrize(
    "label,filler",
    [
        ("slab", slab(length=0.5, thickness=0.25)),
        ("rounded", rounded(radius=0.4)),
        ("wedge", wedge(size=0.28)),
    ],
)
def test_corner_filler_over_stem_widths(system: System, stem: float, label: str, filler) -> None:
    from typekernel.draw import Writer

    d = (
        Writer()
        .start((0, 0))
        .line((50, 0))
        .corner("knee", stem=stem)
        .line((50, 50))
        .line((0, 50))
        .close()
        .build()
    )
    before = contour_area_sign(d)
    out = apply_slots(d, system, corners={"knee": filler}, ends={})
    assert out.contours[0].closed, label
    assert contour_area_sign(out) == before, label
