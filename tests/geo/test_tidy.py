"""S1 compile-time tidy: refit dense expand; not heal/blend/seal."""

from __future__ import annotations

from typekernel.anatomy import pen
from typekernel.geo.tidy import tidy_outline
from typekernel.system import Overshoot, System, Zones


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80, "uc": 90},
        slant=0.2,
        tokens={"pen_contrast": 0.55, "pen_angle_deg": 30.0},
    )


def test_bowl_o_budget_after_tidy() -> None:
    drawing = pen.bowl(_system(), cx=200, cy=250, rx=140, ry=160)
    outline = drawing.outline()
    assert len(outline.contours) <= 2
    for c in outline.contours:
        assert len(c.segments) <= 16, [len(x.segments) for x in outline.contours]


def test_tidy_outline_idempotent_enough() -> None:
    drawing = pen.bowl(_system(), cx=200, cy=250, rx=120, ry=140)
    a = tidy_outline(drawing.outline())
    b = tidy_outline(a)
    assert len(a.contours) == len(b.contours)
