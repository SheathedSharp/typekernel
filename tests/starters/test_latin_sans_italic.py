"""P5-3: latin-sans italic partner + family link."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufo2ft")

from typekernel.axes import read_family_identity
from typekernel.cli.build import build_project
from typekernel.project import open_project

STARTER = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans_italic"
ROMAN = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"


def test_control_glyphs_evaluate() -> None:
    with open_project(STARTER) as session:
        assert {"n", "o", "e", "i", "H", "O"} <= set(session.specs())
        for name in ("n", "o", "e", "i", "H", "O"):
            g = session.glyph(name)
            assert g.outline.contours
            assert g.advance > 0


def test_proportions_match_latin_sans_zones() -> None:
    with open_project(STARTER) as italic, open_project(ROMAN) as roman:
        assert italic.project.system.zones.x == roman.project.system.zones.x
        assert italic.project.system.zones.cap == roman.project.system.zones.cap
        assert italic.project.system.stem["lc"] == roman.project.system.stem["lc"]
        assert italic.project.system.slant != 0.0
        assert roman.project.system.slant == 0.0


def test_family_link_roman_italic(tmp_path: Path) -> None:
    from typekernel.starters.latin_sans.family import FAMILY, link_built_pair

    _rf, roman_build = build_project(ROMAN, out_dir=tmp_path / "roman", formats=("ttf",))
    _if, italic_build = build_project(STARTER, out_dir=tmp_path / "italic", formats=("ttf",))
    roman_bin = next(iter(roman_build.binaries.values()))
    italic_bin = next(iter(italic_build.binaries.values()))
    link_built_pair(roman_bin, italic_bin)
    r = read_family_identity(roman_bin)
    i = read_family_identity(italic_bin)
    assert r["typo_family_id16"] == i["typo_family_id16"] == FAMILY.name
    assert r["typo_subfamily_id17"] == "Regular"
    assert i["typo_subfamily_id17"] == "Italic"
    assert i["fs_selection_italic"] is True
    assert "ital" in r["stat_axes"] and "ital" in i["stat_axes"]
