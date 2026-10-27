"""Compile path for Font built from System (no DesignContext)."""

from __future__ import annotations

import pytest

from typekernel.draw import Writer
from typekernel.font import Font
from typekernel.system import Overshoot, System, Zones

ufoLib2 = pytest.importorskip("ufoLib2")


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80},
    )


def test_font_to_ufo_from_system_font() -> None:
    from typekernel.compile import font_to_ufo

    font = Font.from_system(_system(), "Sys Export")
    d = (
        Writer()
        .start((0.0, 0.0))
        .line((100.0, 0.0))
        .line((100.0, 100.0))
        .line((0.0, 100.0))
        .close()
        .build()
    )
    font.add_drawing("fixture.box", d, advance=120.0)
    ufo = font_to_ufo(font)
    assert "fixture.box" in ufo
    assert ufo["fixture.box"].width == 120
    assert ufo.info.familyName == "Sys Export"
    