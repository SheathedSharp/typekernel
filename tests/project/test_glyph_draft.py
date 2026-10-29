"""GlyphSpec v2 / GlyphDraft (roadmap P1-3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.compile.ufo_export import write_font_to_ufo
from typekernel.project import GlyphDraft, glyph, open_project
from typekernel.project.registry import GlyphSpec, registration_target
from typekernel.system import TRAITS, System, UnknownTraitError


def _write_anchor_project(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "glyphs").mkdir()
    (root / "system.py").write_text(
        "from typekernel.system import Overshoot, System, Zones\n"
        "system = System(upm=1000, zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200), "
        "overshoot=Overshoot(round=12, pointed=10), stem={'lc': 80})\n",
        encoding="utf-8",
    )
    (root / "project.py").write_text(
        "from system import system\n"
        "from typekernel.project import FamilyInfo, Project\n"
        "PROJECT = Project(info=FamilyInfo(family='Draft'), system=system, glyphs='glyphs')\n",
        encoding="utf-8",
    )
    (root / "glyphs" / "syn_base.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import GlyphDraft, glyph\n"
        "from typekernel.system import System\n"
        "\n"
        "@glyph('syn.base', unicodes=(0xE000,), traits=('x-height', 'flat-top'), group='fixture')\n"
        "def syn_base(system: System):\n"
        "    d = (\n"
        "        Writer().start((0, 0)).line((100, 0)).line((100, 100)).line((0, 100)).close().build()\n"
        "    )\n"
        "    return GlyphDraft(drawing=d, anchors={'top': (50.0, 100.0)}, note='test base')\n"
        "\n"
        "@glyph('syn.mark', unicodes=(), traits=('mark',), group='fixture')\n"
        "def syn_mark(system: System):\n"
        "    d = (\n"
        "        Writer().start((0, 0)).line((20, 0)).line((20, 20)).line((0, 20)).close().build()\n"
        "    )\n"
        "    return GlyphDraft(drawing=d, anchors={'_top': (10.0, 0.0)})\n",
        encoding="utf-8",
    )
    return root


def test_unknown_trait_rejected_at_decoration() -> None:

    bucket: dict[str, GlyphSpec] = {}
    with registration_target(bucket), pytest.raises(UnknownTraitError, match="unknown trait"):

        @glyph("syn.bad", traits=("not-a-real-trait",))
        def bad(system: System):
            from typekernel.draw import Writer

            return Writer().start((0, 0)).line((1, 0)).line((1, 1)).line((0, 1)).close().build()


def test_traits_vocabulary_covers_architecture_list() -> None:
    assert "x-height" in TRAITS
    assert "no-stem" in TRAITS
    assert "mark" in TRAITS


def test_anchors_reach_ufo_and_empty_unicodes_skip_cmap(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    root = _write_anchor_project(tmp_path / "proj")
    with open_project(root) as session:
        base = session.glyph("syn.base")
        assert base.unicodes == (0xE000,)
        assert len(base.anchors) == 1
        assert base.anchors[0].name == "top"
        assert base.anchors[0].y == pytest.approx(100.0)

        mark = session.glyph("syn.mark")
        assert mark.unicodes == ()
        assert mark.anchors[0].name == "_top"

        draft = session.evaluate("syn.base")
        assert isinstance(draft, GlyphDraft)
        assert draft.note == "test base"

        font = session.font(family_name="Draft")

    ufo_path = tmp_path / "out.ufo"
    write_font_to_ufo(font, ufo_path)
    from ufoLib2 import Font as UfoFont

    ufo = UfoFont.open(ufo_path)
    assert "syn.base" in ufo
    assert any(a.name == "top" for a in ufo["syn.base"].anchors)
    # unicodes=() must not appear in cmap
    cmap = {cp for g in ufo for cp in g.unicodes}
    assert 0xE000 in cmap
    # mark has no unicodes
    assert ufo["syn.mark"].unicodes == []


def test_drawing_return_still_works(tmp_path: Path) -> None:
    """Builders that return Drawing (not GlyphDraft) keep working."""
    root = tmp_path / "proj"
    root.mkdir()
    (root / "glyphs").mkdir()
    (root / "system.py").write_text(
        "from typekernel.system import Overshoot, System, Zones\n"
        "system = System(upm=1000, zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200), "
        "overshoot=Overshoot(round=12, pointed=10), stem={'lc': 80})\n",
        encoding="utf-8",
    )
    (root / "project.py").write_text(
        "from system import system\n"
        "from typekernel.project import FamilyInfo, Project\n"
        "PROJECT = Project(info=FamilyInfo(family='Plain'), system=system, glyphs='glyphs')\n",
        encoding="utf-8",
    )
    (root / "glyphs" / "syn_plain.py").write_text(
        "from typekernel.draw import Writer\n"
        "from typekernel.project import glyph\n"
        "from typekernel.system import System\n"
        "\n"
        "@glyph('syn.plain', group='fixture')\n"
        "def syn_plain(system: System):\n"
        "    return Writer().start((0, 0)).line((40, 0)).line((40, 40)).line((0, 40)).close().build()\n",
        encoding="utf-8",
    )
    with open_project(root) as session:
        draft = session.evaluate("syn.plain")
        assert isinstance(draft, GlyphDraft)
        assert draft.anchors == {}
        g = session.glyph("syn.plain")
        assert g.advance == pytest.approx(40.0)
