"""CLI scaffold / build / proof (ARCHITECTURE.md M2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.cli.__main__ import main
from typekernel.cli.load import load_project
from typekernel.cli.new import create_project


def _write_synthetic_glyphs(glyphs: Path) -> None:
    glyphs.mkdir(parents=True, exist_ok=True)
    (glyphs / "syn_box.py").write_text(
        '''\
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("syn.box", group="fixture")
def syn_box(system: System):
    s = float(system.stem["lc"])
    w = 100.0 + s * 0.1
    h = float(system.zones.x)
    return (
        Writer()
        .start((0.0, 0.0))
        .line((w, 0.0))
        .line((w, h))
        .line((0.0, h))
        .close()
        .build()
    )
''',
        encoding="utf-8",
    )


def test_tk_new_creates_empty_layout(tmp_path: Path) -> None:
    root = create_project("demo_font", parent=tmp_path)
    assert (root / "system.py").is_file()
    assert (root / "font.py").is_file()
    assert (root / "glyphs").is_dir()
    project = load_project(root)
    project.discover()
    assert project.specs() == {}


def test_tk_new_via_main(tmp_path: Path) -> None:
    assert main(["new", "via_main", "--parent", str(tmp_path)]) == 0
    assert (tmp_path / "via_main" / "font.py").is_file()


def test_tk_build_otf_with_synthetic_glyph(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    root = create_project("syn_proj", parent=tmp_path)
    _write_synthetic_glyphs(root / "glyphs")
    assert main(["build", str(root), "--out", str(root / "build")]) == 0
    otfs = list((root / "build").glob("*.otf"))
    assert len(otfs) == 1
    # fontTools can open it
    from fontTools.ttLib import TTFont

    tt = TTFont(otfs[0])
    assert "syn.box" in tt.getGlyphOrder()
    assert ".notdef" in tt.getGlyphOrder()


def test_tk_proof_control_writes_png(tmp_path: Path) -> None:
    pytest.importorskip("PIL")
    pytest.importorskip("ufoLib2")
    root = create_project("proof_proj", parent=tmp_path)
    _write_synthetic_glyphs(root / "glyphs")
    assert main(["build", str(root)]) == 0
    assert main(["proof", "control", str(root), "--out", str(root / "proofs")]) == 0
    assert (root / "proofs" / "control.png").is_file()


def test_tk_diff_snapshot_and_change_detection(tmp_path: Path) -> None:
    """tk diff uses outline_hash; not a golden gate (ARCHITECTURE.md §3.3)."""
    root = create_project("diff_proj", parent=tmp_path)
    _write_synthetic_glyphs(root / "glyphs")
    snap = root / "build" / "glyph_hashes.json"
    assert main(["diff", str(root), "--snapshot", str(snap)]) == 0
    assert snap.is_file()
    # unchanged → empty report
    assert main(["diff", str(root), "--against", str(snap)]) == 0
    # mutate glyph geometry
    syn = (root / "glyphs" / "syn_box.py").read_text(encoding="utf-8")
    (root / "glyphs" / "syn_box.py").write_text(
        syn.replace("w = 100.0 + s * 0.1", "w = 140.0 + s * 0.1"),
        encoding="utf-8",
    )
    from typekernel.cli.diff_cmd import diff_project, format_diff

    result = diff_project(root, against=snap)
    assert "syn.box" in result["changed"]
    assert "changed" in format_diff(result)
