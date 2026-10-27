"""Glyph.from_drawing / system helpers (post-parts)."""

from __future__ import annotations

import pytest

from typekernel.draw import Writer
from typekernel.font.glyph import (
    Glyph,
    glyph_name_for_char,
    notdef_glyph_from_system,
    space_glyph_from_system,
)
from typekernel.system import Overshoot, System, Zones


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80},
    )


def test_from_drawing_and_names() -> None:
    d = (
        Writer()
        .start((0, 0))
        .line((100, 0))
        .line((100, 100))
        .line((0, 100))
        .close()
        .build()
    )
    g = Glyph.from_drawing("syn.box", d, advance=120.0)
    assert g.name == "syn.box"
    assert g.advance == 120.0
    assert glyph_name_for_char("a") == "a"
    assert glyph_name_for_char(",") == "comma"


def test_notdef_and_space_from_system() -> None:
    s = _system()
    nd = notdef_glyph_from_system(s)
    assert nd.name == ".notdef"
    assert nd.advance > 0
    sp = space_glyph_from_system(s)
    assert sp.name == "space"
    assert sp.advance == pytest.approx(0.5 * s.zones.x)
    assert sp.unicodes == (0x20,)
