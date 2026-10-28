"""End-to-end: synthetic-only temp project → OTF (ARCHITECTURE.md「验收方式」)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.cli.build import build_project
from typekernel.cli.new import create_project


def _add_glyphs(glyphs: Path) -> None:
    (glyphs / "syn_arch.py").write_text(
        '''\
from typekernel.draw import Writer, tensioned_arc
from typekernel.project import glyph
from typekernel.system import System


@glyph("syn.arch", group="fixture")
def syn_arch(system: System):
    left, right = 0.0, 100.0
    top = float(system.zones.x)
    arch = tensioned_arc(
        (left, top),
        (1.0, 0.8),
        (right, top),
        (1.0, -0.8),
        tension=0.55,
    )
    return (
        Writer()
        .start((left, 0.0))
        .line((left, top))
        .corner("stem.l.top")
        .fragment(arch, prefix="arch")
        .corner("stem.r.top")
        .line((right, 0.0))
        .line((left, 0.0))
        .close()
        .build()
    )
''',
        encoding="utf-8",
    )
    (glyphs / "fixture_stem.py").write_text(
        '''\
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("fixture.stem", group="fixture")
def fixture_stem(system: System):
    s = float(system.stem["lc"])
    return (
        Writer()
        .start((0.0, 0.0))
        .line((s, 0.0))
        .line((s, 100.0))
        .line((0.0, 100.0))
        .close()
        .build()
    )
''',
        encoding="utf-8",
    )


def test_synthetic_temp_project_builds_otf(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    root = create_project("e2e_syn", parent=tmp_path)
    _add_glyphs(root / "glyphs")
    font, result = build_project(root, out_dir=root / "build", formats=("otf",))
    assert "syn.arch" in font
    assert "fixture.stem" in font
    assert result.binaries["otf"].is_file()
    from fontTools.ttLib import TTFont

    tt = TTFont(result.binaries["otf"])
    names = set(tt.getGlyphOrder())
    assert {"syn.arch", "fixture.stem", ".notdef", "space"} <= names
