"""Marks directory discovery and zero-advance mark glyphs."""

from __future__ import annotations

from pathlib import Path

from typekernel.project import open_project


def _write_project(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "glyphs").mkdir()
    (root / "marks").mkdir()
    (root / "system.py").write_text(
        "from typekernel.system import Overshoot, System, Zones\n"
        "system = System(\n"
        "    upm=1000,\n"
        "    zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),\n"
        "    overshoot=Overshoot(round=12, pointed=10),\n"
        '    stem={"lc": 80},\n'
        ")\n",
        encoding="utf-8",
    )
    (root / "project.py").write_text(
        "from system import system\n"
        "from typekernel.project import FamilyInfo, Project\n"
        "PROJECT = Project(\n"
        "    info=FamilyInfo(family='MarksTrial'),\n"
        "    system=system,\n"
        "    glyphs='glyphs',\n"
        "    marks='marks',\n"
        ")\n",
        encoding="utf-8",
    )
    (root / "glyphs" / "syn_base.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import GlyphDraft, glyph\n"
        "from typekernel.system import System\n"
        "\n"
        '@glyph("syn.base", group="fixture")\n'
        "def syn_base(system: System):\n"
        "    d = (\n"
        "        Writer().start((0,0)).line((40,0)).line((40,100))"
        ".line((0,100)).close().build()\n"
        "    )\n"
        "    return GlyphDraft(drawing=d, anchors={'top': (20.0, 100.0)})\n",
        encoding="utf-8",
    )
    (root / "marks" / "syn_mark.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import GlyphDraft, glyph\n"
        "from typekernel.system import System\n"
        "\n"
        '@glyph("syn.mark", unicodes=(), group="marks", traits=("mark",))\n'
        "def syn_mark(system: System):\n"
        "    d = (\n"
        "        Writer().start((-5,10)).line((5,10)).line((5,20))"
        ".line((-5,20)).close().build()\n"
        "    )\n"
        "    return GlyphDraft(drawing=d, anchors={'_top': (0.0, 0.0)})\n",
        encoding="utf-8",
    )


def test_marks_dir_discovered_and_mark_advance_zero(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    _write_project(root)
    with open_project(root) as session:
        specs = session.specs()
        assert "syn.base" in specs
        assert "syn.mark" in specs
        assert "mark" in specs["syn.mark"].traits
        mark = session.glyph("syn.mark")
        assert mark.advance == 0.0
        assert any(a.name == "_top" for a in mark.anchors)
        base = session.glyph("syn.base")
        assert any(a.name == "top" for a in base.anchors)
