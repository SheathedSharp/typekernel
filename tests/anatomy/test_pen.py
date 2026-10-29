"""anatomy.pen cubic stroke API; starters keep hash-stable shims."""

from __future__ import annotations

import pytest

from typekernel.anatomy import pen
from typekernel.system import Overshoot, System, Zones


def _system(*, slant: float = 0.2) -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80, "uc": 90},
        slant=slant,
        tokens={"pen_contrast": 0.55, "pen_angle_deg": 30.0},
    )


def test_stroke_rejects_polyline_points() -> None:
    with pytest.raises(TypeError, match="CubicCenterline|Fragment"):
        pen.stroke(_system(), [(0.0, 0.0), (0.0, 100.0)])


def test_stroke_accepts_cubic_centerline() -> None:
    system = _system()
    cubic = pen.slanted_cubic_from_points([(120.0, 0.0), (120.0, 500.0)], system)
    drawing = pen.stroke(system, cubic)
    assert drawing.outline().contours


def test_bowl_and_open_bowl_cubic() -> None:
    system = _system()
    closed = pen.bowl(system, cx=200, cy=250, rx=120, ry=140)
    opened = pen.open_bowl(system, cx=200, cy=250, rx=120, ry=140, open_side="right")
    assert closed.outline().contours
    assert opened.outline().contours


def test_pen_dot_and_flourish() -> None:
    system = _system()
    system = System(
        upm=system.upm,
        zones=system.zones,
        overshoot=system.overshoot,
        stem=system.stem,
        slant=system.slant,
        tokens={**dict(system.tokens), "flourish_depth": 40.0, "dot_radius": 28.0},
    )
    dot = pen.pen_dot(system, 100.0, 600.0)
    assert dot.outline().contours
    frag = pen.flourish_exit(system, 100.0, 0.0, (40.0, -30.0))
    drawn = pen.stroke_fragment(system, frag)
    assert drawn.outline().contours
