"""glyphs_italic/ loads for italic masters."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.geo.outline import bounds
from typekernel.project import open_project


def _write_minimal(root: Path) -> None:
    glyphs = root / "glyphs"
    italic = root / "glyphs_italic"
    glyphs.mkdir()
    italic.mkdir()
    (root / "system.py").write_text(
        "from typekernel.system import Overshoot, System, Zones\n"
        "from typekernel.project import Master\n"
        "\n"
        "roman = System(\n"
        "    upm=1000,\n"
        "    zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),\n"
        "    overshoot=Overshoot(round=12, pointed=10),\n"
        '    stem={"lc": 80},\n'
        "    slant=0.0,\n"
        ")\n"
        "italic = roman.tuned(slant=0.2)\n"
        "system = roman\n"
        "masters = (\n"
        "    Master('Roman', roman),\n"
        "    Master('Italic', italic),\n"
        ")\n",
        encoding="utf-8",
    )
    (root / "project.py").write_text(
        "from system import masters, system\n"
        "from typekernel.axes import MasterSpec\n"
        "from typekernel.project import FamilyInfo, Project\n"
        "_MASTER_LOCATIONS = {'Roman': {'wght': 400}, 'Italic': {'wght': 400, 'ital': 1}}\n"
        "PROJECT = Project(\n"
        "    info=FamilyInfo(family='ItalicDirTrial'),\n"
        "    system=system,\n"
        "    glyphs='glyphs',\n"
        "    glyphs_italic='glyphs_italic',\n"
        "    masters=tuple(\n"
        "        MasterSpec(m.name, _MASTER_LOCATIONS[m.name], m.system) for m in masters\n"
        "    ),\n"
        ")\n",
        encoding="utf-8",
    )
    # Roman bar width 100
    (glyphs / "syn_bar.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import glyph\n"
        "from typekernel.system import System\n"
        "\n"
        '@glyph("syn.bar", group="fixture")\n'
        "def syn_bar(system: System):\n"
        "    return (\n"
        "        Writer().start((0, 0)).line((100, 0)).line((100, 40))"
        ".line((0, 40)).close().build()\n"
        "    )\n",
        encoding="utf-8",
    )
    # Italic bar width 160 (distinct geometry)
    (italic / "syn_bar.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import glyph\n"
        "from typekernel.system import System\n"
        "\n"
        '@glyph("syn.bar", group="fixture")\n'
        "def syn_bar(system: System):\n"
        "    return (\n"
        "        Writer().start((0, 0)).line((160, 0)).line((160, 40))"
        ".line((0, 40)).close().build()\n"
        "    )\n",
        encoding="utf-8",
    )


def test_italic_master_uses_glyphs_italic_outline(tmp_path: Path) -> None:
    root = tmp_path / "italproj"
    root.mkdir()
    _write_minimal(root)
    with open_project(root) as session:
        assert "syn.bar" in session.specs()
        assert "syn.bar" in session.italic_specs()
        roman = session.evaluate("syn.bar", master="Roman").drawing
        italic = session.evaluate("syn.bar", master="Italic").drawing
        _, _, rx, _ = bounds(roman.outline())
        _, _, ix, _ = bounds(italic.outline())
        assert rx == pytest.approx(100.0)
        assert ix == pytest.approx(160.0)


def test_roman_master_ignores_glyphs_italic(tmp_path: Path) -> None:
    root = tmp_path / "italproj2"
    root.mkdir()
    _write_minimal(root)
    with open_project(root) as session:
        d = session.evaluate("syn.bar", master="Roman").drawing
        _, _, mx, _ = bounds(d.outline())
        assert mx == pytest.approx(100.0)
