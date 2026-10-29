"""roman + synthetic italic share typographic family / STAT ital."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufo2ft")

from typekernel.axes import FamilyMember, FamilySpec, link_family, read_family_identity
from typekernel.cli.build import build_project
from typekernel.compile import build_font, oblique_font


def test_latin_sans_links_with_synthetic_oblique(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    font, _ = build_project(root, out_dir=tmp_path / "roman", formats=("ttf",))
    roman_bin = tmp_path / "roman" / "LatinSans-Regular.ttf"
    # build_project may use a different stem — find the ttf
    romans = list((tmp_path / "roman").glob("*.ttf"))
    assert romans, "expected a roman TTF from build_project"
    roman_bin = romans[0]

    italic_font = oblique_font(font, 12.0, style_name="Italic")
    italic_build = build_font(italic_font, tmp_path / "italic", formats=("ttf",))
    italic_bin = next(iter(italic_build.binaries.values()))

    family = FamilySpec(
        name="Latin Sans",
        members=(
            FamilyMember("Regular", italic=False, weight_class=400),
            FamilyMember("Italic", italic=True, weight_class=400),
        ),
    )
    link_family(
        (
            (family.members[0], roman_bin),
            (family.members[1], italic_bin),
        ),
        family,
    )

    roman_id = read_family_identity(roman_bin)
    italic_id = read_family_identity(italic_bin)

    assert roman_id["typo_family_id16"] == italic_id["typo_family_id16"] == "Latin Sans"
    assert roman_id["typo_subfamily_id17"] == "Regular"
    assert italic_id["typo_subfamily_id17"] == "Italic"
    assert roman_id["subfamily_id2"] == "Regular"
    assert italic_id["subfamily_id2"] == "Italic"
    assert "ital" in roman_id["stat_axes"]
    assert "ital" in italic_id["stat_axes"]
    assert 0.0 in roman_id["stat_ital_values"]
    assert 1.0 in italic_id["stat_ital_values"]
    assert roman_id["fs_selection_italic"] is False
    assert italic_id["fs_selection_italic"] is True
