"""A-class AnchorsCheck for mark attachment and composite refs."""

from __future__ import annotations

from pathlib import Path

from typekernel.diagnose import audit_project
from typekernel.project import open_project


def _write(root: Path, *, with_attach: bool, with_composite: bool) -> None:
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
    composites = (
        "from typekernel.project import Composite\n"
        "COMPOSITES = {'syn.comp': Composite(base='syn.base', marks=('syn.mark@top',))}\n"
        if with_composite
        else "COMPOSITES = {}\n"
    )
    (root / "composites.py").write_text(composites, encoding="utf-8")
    (root / "project.py").write_text(
        "from system import system\n"
        "from composites import COMPOSITES\n"
        "from typekernel.project import FamilyInfo, Project\n"
        "PROJECT = Project(\n"
        "    info=FamilyInfo(family='AnchorTrial'),\n"
        "    system=system,\n"
        "    glyphs='glyphs',\n"
        "    marks='marks',\n"
        "    composites=COMPOSITES,\n"
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
        "    d = Writer().start((0,0)).line((40,0)).line((40,100))"
        ".line((0,100)).close().build()\n"
        "    return GlyphDraft(drawing=d, anchors={'top': (20.0, 100.0)})\n",
        encoding="utf-8",
    )
    anchors = "{'_top': (0.0, 0.0)}" if with_attach else "{}"
    (root / "marks" / "syn_mark.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import GlyphDraft, glyph\n"
        "from typekernel.system import System\n"
        "\n"
        '@glyph("syn.mark", unicodes=(), group="marks", traits=("mark",))\n'
        "def syn_mark(system: System):\n"
        "    d = Writer().start((-5,10)).line((5,10)).line((5,20))"
        ".line((-5,20)).close().build()\n"
        f"    return GlyphDraft(drawing=d, anchors={anchors})\n",
        encoding="utf-8",
    )


def test_mark_without_attachment_is_error(tmp_path: Path) -> None:
    root = tmp_path / "bad"
    _write(root, with_attach=False, with_composite=False)
    report = audit_project(root)
    assert any(
        f.check == "anchors.mark_attachment" and f.level == "error"
        for f in report.findings
    )


def test_composite_anchor_ok(tmp_path: Path) -> None:
    root = tmp_path / "ok"
    _write(root, with_attach=True, with_composite=True)
    report = audit_project(root)
    assert not any(f.check.startswith("anchors.") and f.level == "error" for f in report.findings)
