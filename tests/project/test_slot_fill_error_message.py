"""Session.evaluate wraps slot failures as GlyphBuildError."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.project import GlyphBuildError, open_project


def test_evaluate_wraps_slot_fill_error_with_glyph_and_tag(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    root.mkdir()
    glyphs = root / "glyphs"
    glyphs.mkdir()
    (root / "system.py").write_text(
        "from typekernel.system import Overshoot, System, Zones\n"
        "system = System(upm=1000, zones=Zones(x=500, cap=700, asc=750, desc=-200), "
        "overshoot=Overshoot(round=12, pointed=10), stem={'lc': 80})\n",
        encoding="utf-8",
    )
    (root / "project.py").write_text(
        "from typekernel.draw import CornerFill, Fragment\n"
        "from typekernel.geo.point import Point\n"
        "from typekernel.geo.segment import LineSegment\n"
        "from typekernel.project import FamilyInfo, Project\n"
        "from system import system\n"
        "\n"
        "def bad_fill(site, system):\n"
        "    trim = 2.0\n"
        "    a = Point(site.point.x - 100.0, site.point.y)\n"
        "    b = site.point_out(trim)\n"
        "    return CornerFill(trim_in=trim, trim_out=trim, "
        "path=Fragment((LineSegment(a, b),)))\n"
        "\n"
        "PROJECT = Project(\n"
        "    info=FamilyInfo(family='SlotTest'),\n"
        "    system=system,\n"
        "    glyphs='glyphs',\n"
        "    corners={'knee': bad_fill},\n"
        ")\n",
        encoding="utf-8",
    )
    (glyphs / "syn_box.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import glyph\n"
        "\n"
        "@glyph('syn.box')\n"
        "def syn_box(system):\n"
        "    return (\n"
        "        Writer()\n"
        "        .start((0, 0))\n"
        "        .line((20, 0))\n"
        "        .corner('knee')\n"
        "        .line((20, 20))\n"
        "        .line((0, 20))\n"
        "        .close()\n"
        "        .build()\n"
        "    )\n",
        encoding="utf-8",
    )
    with open_project(root) as session:
        with pytest.raises(GlyphBuildError, match=r"glyph 'syn\.box'.*slot 'knee'") as ei:
            session.evaluate("syn.box")
        assert ei.value.tag == "knee"
        assert ei.value.glyph == "syn.box"
