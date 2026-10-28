"""latin-humanist-italic starter control glyphs via skeleton+pen."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.cli.build import build_project, build_variable_project
from typekernel.cli.load import load_project
from typekernel.cli.new import create_project
from typekernel.cli.proof_cmd import proof_project

STARTER = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "typekernel"
    / "starters"
    / "latin_humanist_italic"
)


def test_starter_tree_has_control_files() -> None:
    assert (STARTER / "system.py").is_file()
    assert (STARTER / "elements.py").is_file()
    assert (STARTER / "font.py").is_file()
    for rel in (
        "glyphs/lower/n.py",
        "glyphs/lower/o.py",
        "glyphs/upper/H.py",
        "glyphs/upper/O.py",
    ):
        assert (STARTER / rel).is_file()


def test_starter_uses_construct_plugin_not_writer_outlines() -> None:
    """Glyph sources expand skeleton+pen; elements imports construct plugin."""
    elements = (STARTER / "elements.py").read_text(encoding="utf-8")
    assert "expand_skeleton" in elements or "plugins.construct" in elements
    n_src = (STARTER / "glyphs" / "lower" / "n.py").read_text(encoding="utf-8")
    assert "Writer" not in n_src
    assert "stroke" in n_src


def test_discover_evaluate_control_set() -> None:
    project = load_project(STARTER)
    project.discover()
    assert {"n", "o", "H", "O"} <= set(project.specs())
    for name in ("n", "o", "H", "O"):
        drawing = project.evaluate(name)
        assert len(drawing.contours) >= 1
        assert drawing.roles[0] == "ink"
        glyph = project.to_glyph(name)
        assert glyph.unicodes == (ord(name),)
        assert glyph.advance > 0
    # Closed bowls expose a counter contour.
    o = project.evaluate("o")
    assert "counter" in o.roles
    O = project.evaluate("O")
    assert "counter" in O.roles


def test_tk_new_humanist_italic_builds_otf(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    root = create_project("demo_hi", parent=tmp_path, starter="latin-humanist-italic")
    assert (root / "elements.py").is_file()
    assert (root / "glyphs" / "lower" / "n.py").is_file()
    system_text = (root / "system.py").read_text(encoding="utf-8")
    assert 'FAMILY_NAME = "Demo Hi"' in system_text
    font, result = build_project(root, out_dir=root / "build", formats=("otf",))
    names = {g.name for g in font}
    assert {"n", "o", "H", "O", ".notdef", "space"} <= names
    otf = result.binaries["otf"]
    assert otf.is_file()
    from fontTools.ttLib import TTFont

    cmap = TTFont(otf).getBestCmap()
    assert all(ord(c) in cmap for c in "noHO")


def test_proof_control_png(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    pytest.importorskip("PIL")
    root = create_project("proof_hi", parent=tmp_path, starter="latin-humanist-italic")
    build_project(root, out_dir=root / "build", formats=("otf",))
    written = proof_project(root, "control", out_dir=root / "proofs")
    assert len(written) == 1
    assert written[0].is_file()
    assert written[0].stat().st_size > 100


def test_n_group_glyphs_evaluate() -> None:
    project = load_project(STARTER)
    project.discover()
    for name in ("h", "m", "u", "i", "l"):
        drawing = project.evaluate(name)
        assert len(drawing.contours) >= 1
        assert drawing.roles[0] == "ink"
        assert project.to_glyph(name).advance > 0


def test_o_group_glyphs_evaluate() -> None:
    project = load_project(STARTER)
    project.discover()
    for name in ("a", "b", "d", "e", "p", "q"):
        drawing = project.evaluate(name)
        assert len(drawing.contours) >= 2  # stem ink + bowl (+counter)
        assert "ink" in drawing.roles
        assert project.to_glyph(name).advance > 0



def test_masters_signature_compatible() -> None:
    """Light / Regular / Bold drawings share signatures for every glyph."""
    from typekernel.starters.latin_humanist_italic.system import (
        MASTER_LOCATIONS,
        _weight_system,
        masters,
        system,
    )

    assert len(masters) == 2
    assert set(MASTER_LOCATIONS) >= {"Light", "Regular", "Bold"}
    project = load_project(STARTER)
    project.discover()
    names = sorted(project.specs())
    scales = {
        "Light": 0.62,
        "Regular": 1.0,
        "Bold": 1.38,
    }
    for name in names:
        sigs = []
        for label, scale in scales.items():
            sys_w = system if scale == 1.0 else _weight_system(system, scale)
            from typekernel.project import Project

            p = Project(sys_w, STARTER / "glyphs", masters=())
            p.discover()
            sigs.append(p.evaluate(name).signature())
        assert sigs[0] == sigs[1] == sigs[2], name


def test_variable_font_builds(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    root = create_project("demo_hi_vf", parent=tmp_path, starter="latin-humanist-italic")
    # Starter copy includes masters from the template.
    from typekernel.cli.load import load_project as _lp

    proj = _lp(root)
    assert len(proj.masters) == 2
    _masters, result = build_variable_project(root, out_dir=root / "build", formats=("ttf",))
    assert "ttf" in result.binaries
    assert result.binaries["ttf"].is_file()
