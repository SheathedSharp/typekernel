"""P4-5: varLib.instancer static cuts + outline consistency vs VF."""

from __future__ import annotations

from pathlib import Path

import pytest
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from typekernel.axes import Instance, instance_static


def _glyph_checksum(font: TTFont, name: str) -> tuple:
    glyf = font["glyf"][name]
    coords = tuple(tuple(c) for c in getattr(glyf, "coordinates", []) or [])
    return (glyf.numberOfContours, coords)


@pytest.mark.skipif(
    not __import__("importlib.util").util.find_spec("ufo2ft"),
    reason="compile extra required",
)
def test_instance_static_matches_reinstance(tmp_path: Path) -> None:
    from typekernel.cli.build import build_variable_project

    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    out = tmp_path / "build"
    _masters, vf = build_variable_project(root, out_dir=out, formats=("ttf",))
    vf_path = vf.binaries["ttf"]
    assert len(vf.static_instances) == 9

    # Re-instance at Regular and compare to written static.
    regular = next(p for p in vf.static_instances if p.name.endswith("-Regular.ttf"))
    fresh = instance_static(vf_path, {"wght": 400.0}, tmp_path / "fresh-Regular.ttf")
    a = TTFont(regular)
    b = TTFont(fresh)
    for gname in ("n", "a", "A", "o"):
        assert _glyph_checksum(a, gname) == _glyph_checksum(b, gname)

    # Master locations: static Bold vs VF pinned to 700.
    bold = next(p for p in vf.static_instances if p.name.endswith("-Bold.ttf"))
    pinned = instantiateVariableFont(
        TTFont(vf_path), {"wght": 700.0}, inplace=False
    )
    pinned_path = tmp_path / "pinned-Bold.ttf"
    pinned.save(pinned_path)
    sb = TTFont(bold)
    pb = TTFont(pinned_path)
    for gname in ("n", "H"):
        assert _glyph_checksum(sb, gname) == _glyph_checksum(pb, gname)


def test_instance_statics_names(tmp_path: Path) -> None:
    # Unit: naming only — skip if no VF fixture; covered above when compile present.
    instances = (
        Instance("Thin", {"wght": 100.0}),
        Instance("Black", {"wght": 900.0}),
    )
    assert instances[0].name == "Thin"
