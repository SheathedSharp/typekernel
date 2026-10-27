"""Font / Glyph accept System and Drawing (ARCHITECTURE.md §5 / M2 task 12)."""

from __future__ import annotations

import pytest

from typekernel.draw import Writer
from typekernel.font import (
    Font,
    FontInfo,
    Glyph,
    alignment_zones_from_system,
    notdef_glyph_from_system,
    space_glyph_from_system,
)
from typekernel.system import Overshoot, System, Zones


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=520, cap=700, asc=740, desc=-210),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 84, "lc_h": 70, "uc": 92},
        tokens={"thin": 70},
    )


def _box(w: float = 100.0, h: float = 100.0):
    return (
        Writer()
        .start((0.0, 0.0))
        .line((w, 0.0))
        .line((w, h))
        .line((0.0, h))
        .close()
        .build()
    )


def test_glyph_from_drawing() -> None:
    d = _box(80, 120)
    g = Glyph.from_drawing("fixture.box", d, advance=100.0)
    assert g.name == "fixture.box"
    assert g.advance == 100.0
    assert g.outline.contour_count == 1
    assert g.unicodes == ()


def test_font_from_system_seeds_notdef_and_space() -> None:
    s = _system()
    font = Font.from_system(s, "Sys Sans", space_width=250.0)
    assert font.system is s
    assert font.glyph_order == [".notdef", "space"]
    assert font["space"].advance == 250.0
    assert font.info.units_per_em == 1000
    assert font.info.x_height == 520
    assert font.info.stem_snap_v == (84.0, 70.0, 92.0)
    assert font.info.stem_snap_h == (70.0,)
    assert font.validate() == []


def test_font_add_drawing() -> None:
    font = Font.from_system(_system(), "Sys Sans")
    font.add_drawing("fixture.box", _box(), advance=120.0)
    assert "fixture.box" in font
    assert font["fixture.box"].advance == 120.0


def test_fontinfo_from_system_line_gap() -> None:
    s = _system()
    info = FontInfo.from_system(s, "X", line_height=1.2)
    total = info.ascender - info.descender + info.line_gap
    assert total == pytest.approx(1.2 * s.upm)


def test_alignment_zones_from_system() -> None:
    s = _system()
    blues, others = alignment_zones_from_system(s)
    assert blues[0] == (-12.0, 0.0)
    assert any(abs(lo - 520.0) < 1e-9 for lo, _hi in blues)
    assert others[0][1] == -210.0


def test_notdef_and_space_from_system() -> None:
    s = _system()
    nd = notdef_glyph_from_system(s)
    sp = space_glyph_from_system(s)
    assert nd.name == ".notdef"
    assert nd.outline.contour_count >= 1
    assert sp.name == "space"
    assert sp.advance == pytest.approx(260.0)
