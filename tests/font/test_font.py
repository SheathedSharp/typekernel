"""Font.from_system path (post-parts)."""

from __future__ import annotations

from typekernel.draw import Writer
from typekernel.font import Font, Glyph
from typekernel.font.kerning import KernPair, KernTable
from typekernel.system import Overshoot, System, Zones


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80},
    )


def test_from_system_seeds_notdef_and_space() -> None:
    f = Font.from_system(_system(), "Test Sans", space_width=200)
    assert ".notdef" in f
    assert "space" in f
    assert f["space"].advance == 200
    assert f.glyph_order[0] == ".notdef"


def test_add_drawing_and_kern() -> None:
    f = Font.from_system(_system(), "Test Sans")
    d = (
        Writer()
        .start((40, 0))
        .line((120, 0))
        .line((120, 500))
        .line((40, 500))
        .close()
        .build()
    )
    f.add_drawing("n", d, advance=200, unicodes=(ord("n"),))
    assert "n" in f
    skipped = f.add_kern_table(KernTable((KernPair("n", "n", -10.0),)))
    assert skipped == []
    assert f.kerning[("n", "n")] == -10.0
