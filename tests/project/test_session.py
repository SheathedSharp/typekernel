"""ProjectSession isolation with synthetic projects (no letter glyph names)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.project import open_project


def test_reload_sees_two_edits_within_one_second(tmp_path: Path) -> None:
    """Two edits to elements.py within 1s are both visible to reload()."""
    root = tmp_path / "proj"
    root.mkdir()
    glyphs = root / "glyphs"
    glyphs.mkdir()
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
    (root / "elements.py").write_text("MARKER = 1\n", encoding="utf-8")
    (root / "project.py").write_text(
        "from system import system\n"
        "from typekernel.project import FamilyInfo, Project\n"
        "PROJECT = Project(info=FamilyInfo(family='ReloadTrial'), "
        "system=system, glyphs='glyphs')\n",
        encoding="utf-8",
    )
    (glyphs / "syn_mark.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import glyph\n"
        "from typekernel.system import System\n"
        "import elements\n"
        "\n"
        '@glyph("syn.mark", group="fixture")\n'
        "def syn_mark(system: System):\n"
        "    w = float(elements.MARKER) * 10.0\n"
        "    return (\n"
        "        Writer()\n"
        "        .start((0.0, 0.0))\n"
        "        .line((w, 0.0))\n"
        "        .line((w, 20.0))\n"
        "        .line((0.0, 20.0))\n"
        "        .close()\n"
        "        .build()\n"
        "    )\n",
        encoding="utf-8",
    )

    with open_project(root) as session:
        d0 = session.evaluate("syn.mark")
        assert d0.contours[0].segments[0].points[1].x == pytest.approx(10.0)

        (root / "elements.py").write_text("MARKER = 2\n", encoding="utf-8")
        affected1 = session.reload()
        assert "syn.mark" in affected1
        d1 = session.evaluate("syn.mark")
        assert d1.contours[0].segments[0].points[1].x == pytest.approx(20.0)

        (root / "elements.py").write_text("MARKER = 3\n", encoding="utf-8")
        affected2 = session.reload()
        assert "syn.mark" in affected2
        d2 = session.evaluate("syn.mark")
        assert d2.contours[0].segments[0].points[1].x == pytest.approx(30.0)
