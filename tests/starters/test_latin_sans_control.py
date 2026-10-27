"""M4 task 29: latin-sans starter control glyphs n o H O."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.cli.build import build_project
from typekernel.cli.load import load_project
from typekernel.cli.new import create_project
from typekernel.cli.proof_cmd import proof_project

STARTER = Path(__file__).resolve().parents[2] / "src" / "typekernel" / "starters" / "latin_sans"


def test_starter_tree_has_control_files() -> None:
    assert (STARTER / "system.py").is_file()
    assert (STARTER / "elements.py").is_file()
    assert (STARTER / "font.py").is_file()
    for rel in ("glyphs/lower/n.py", "glyphs/lower/o.py", "glyphs/upper/H.py", "glyphs/upper/O.py"):
        assert (STARTER / rel).is_file()


def test_starter_discover_evaluate_to_glyph() -> None:
    project = load_project(STARTER)
    project.discover()
    assert {"n", "o", "H", "O"} <= set(project.specs())
    expected_uni = {**{ch: ord(ch) for ch in "abcdefghijklmnopqrstuvwxyz"}, "H": 0x48, "O": 0x4F}
    for name, uni in expected_uni.items():
        drawing = project.evaluate(name)
        assert len(drawing.contours) >= 1
        glyph = project.to_glyph(name)
        assert glyph.unicodes == (uni,)
        assert glyph.advance > 0


def test_tk_new_latin_sans_builds_otf(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    root = create_project("demo", parent=tmp_path, starter="latin-sans")
    assert (root / "elements.py").is_file()
    assert (root / "glyphs" / "lower" / "n.py").is_file()
    font, result = build_project(root, out_dir=root / "build", formats=("otf",))
    names = {g.name for g in font}
    assert {"n", "o", "H", "O", ".notdef", "space"} <= names
    otf = result.binaries["otf"]
    assert otf.is_file()
    from fontTools.ttLib import TTFont

    cmap = TTFont(otf).getBestCmap()
    assert all(ord(c) in cmap for c in "noHO")


def test_empty_starter_still_scaffold_only(tmp_path: Path) -> None:
    root = create_project("empty_demo", parent=tmp_path)
    assert (root / "glyphs" / "README.md").is_file()
    assert not (root / "elements.py").exists()


def test_proof_control_png(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    pytest.importorskip("PIL")
    root = create_project("proof_demo", parent=tmp_path, starter="latin-sans")
    build_project(root, out_dir=root / "build", formats=("otf",))
    written = proof_project(root, "control", out_dir=root / "proofs")
    assert len(written) == 1
    assert written[0].is_file()
    assert written[0].stat().st_size > 100
