"""S4 Stroke.through / pointed expand / building blocks."""

from __future__ import annotations

from typekernel.anatomy.stroke import (
    Stroke,
    entry,
    exit,
    expand_pointed,
    expand_stroke,
    loop,
    overstroke,
    pressure_thickness,
)
from typekernel.system import Intent, Overshoot, System, Zones
from typekernel.system.intent import pen_for_intent


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 70, "lc_h": 18, "uc": 80},
        slant=0.18,
        tokens={"pen_contrast": 1.0, "pen_angle_deg": 28.0},
    )


def test_stroke_through_builds_cubics() -> None:
    s = Stroke.through([(0, 0), (100, 200), (200, 50)], tension=1.0)
    assert len(s.centerline.segments) == 2


def test_expand_pointed_thin_up_thick_down() -> None:
    sys = _system()
    # Downstroke
    down = Stroke.through([(100, 400), (100, 0)], tangents=[(0, -1), (0, -1)])
    # Upstroke
    up = Stroke.through([(200, 0), (200, 400)], tangents=[(0, 1), (0, 1)])
    d_down = expand_pointed(down, sys, thin=16, thick=70)
    d_up = expand_pointed(up, sys, thin=16, thick=70)
    assert d_down.outline().contours
    assert d_up.outline().contours
    assert pressure_thickness(0, -1, thin=16, thick=70) > pressure_thickness(0, 1, thin=16, thick=70)


def test_building_blocks_and_intent_pen() -> None:
    assert entry((0, 0), (1, 0)).centerline.segments
    assert exit((0, 0), (1, 0)).centerline.segments
    assert loop((200, 250), rx=80, ry=100).centerline.segments
    assert overstroke((0, 0), (100, 0)).centerline.segments
    pen = pen_for_intent(Intent(tool="pointed", contrast="high", slant="italic"), 70)
    assert pen.contrast == 1.0
    sys = _system()
    st = Stroke.through([(0, 0), (0, 100)])
    assert expand_stroke(st, sys, intent=Intent(tool="pointed")).outline().contours
