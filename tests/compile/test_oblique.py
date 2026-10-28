"""``oblique_font`` shears outlines mechanically — it is not a true italic."""

from __future__ import annotations

import math

import pytest

from typekernel.compile import oblique_font
from typekernel.draw import Writer
from typekernel.font import Font, FontInfo
from typekernel.geo.outline import Outline
from typekernel.system import Overshoot, System, Zones

ANGLE = 12.0


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80},
    )


def _font() -> Font:
    drawing = (
        Writer()
        .start((0, 0))
        .line((0, 400))
        .line((80, 400))
        .line((80, 0))
        .close()
        .build()
    )
    font = Font(
        info=FontInfo(family_name="Syn", style_name="Regular"),
        system=_system(),
    )
    font.add_drawing("syn.bar", drawing, advance=120.0)
    return font


def _points(outline: Outline) -> list[tuple[float, float]]:
    return [(p.x, p.y) for segment in outline.iter_segments() for p in segment.points]


def test_oblique_shifts_every_point_horizontally_by_y() -> None:
    font = _font()
    before = _points(font["syn.bar"].outline)

    sheared = _points(oblique_font(font, ANGLE)["syn.bar"].outline)

    assert len(sheared) == len(before)
    shear = math.tan(math.radians(ANGLE))
    for (bx, by), (ax, ay) in zip(before, sheared, strict=True):
        assert ay == by
        assert ax == pytest.approx(bx + by * shear)


def test_oblique_sets_style_name_and_italic_angle() -> None:
    out = oblique_font(_font(), ANGLE)

    assert out.info.style_name == "Oblique"
    assert out.info.extra["italicAngle"] == -ANGLE


def test_oblique_accepts_a_custom_style_name() -> None:
    out = oblique_font(_font(), ANGLE, style_name="Oblique Bold")

    assert out.info.style_name == "Oblique Bold"


def test_oblique_carries_system_groups_kerning_and_features() -> None:
    font = _font()
    font.groups["public.kern1.syn"] = ("syn.bar",)
    font.kerning[("syn.bar", "syn.bar")] = -30.0
    font.features = "feature liga { } liga;"

    out = oblique_font(font, ANGLE)

    assert out.system is font.system
    assert out.groups == font.groups
    assert out.kerning == font.kerning
    assert out.features == font.features


def test_oblique_leaves_the_source_font_alone() -> None:
    font = _font()
    before = _points(font["syn.bar"].outline)

    oblique_font(font, ANGLE)

    assert _points(font["syn.bar"].outline) == before
    assert font.info.style_name == "Regular"


def test_zero_angle_is_the_identity() -> None:
    font = _font()

    out = oblique_font(font, 0.0)

    assert _points(out["syn.bar"].outline) == _points(font["syn.bar"].outline)
