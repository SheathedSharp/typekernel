"""ProjectSession isolation (target-architecture §3.5 / roadmap P1-1)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from typekernel.project import open_project
from typekernel.qa.outline_hash import outline_hash

LATIN_SANS = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
HUMANIST = (
    Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_humanist_italic"
)


def test_alternate_projects_stable_distinct_hashes() -> None:
    """Alternate latin-sans ↔ humanist-italic 10×; hashes stable and distinct."""
    sans_hashes: list[str] = []
    italic_hashes: list[str] = []
    for _ in range(10):
        with open_project(LATIN_SANS) as session:
            g = session.glyph("n")
            sans_hashes.append(outline_hash(g.outline))
            sys_mod = sys.modules["system"]
            assert Path(sys_mod.__file__).resolve().parent == LATIN_SANS.resolve()
        with open_project(HUMANIST) as session:
            g = session.glyph("n")
            italic_hashes.append(outline_hash(g.outline))
            sys_mod = sys.modules["system"]
            assert Path(sys_mod.__file__).resolve().parent == HUMANIST.resolve()

    assert len(set(sans_hashes)) == 1
    assert len(set(italic_hashes)) == 1
    assert sans_hashes[0] != italic_hashes[0]


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
        ")\n"
        "masters = ()\n"
        'FAMILY_NAME = "ReloadTrial"\n'
        'STYLE_NAME = "Regular"\n',
        encoding="utf-8",
    )
    (root / "elements.py").write_text("MARKER = 1\n", encoding="utf-8")
    (root / "font.py").write_text(
        "from pathlib import Path\n"
        "from typekernel.project import Project\n"
        "from system import masters, system\n"
        "ROOT = Path(__file__).resolve().parent\n"
        "def get_project():\n"
        "    return Project(system, ROOT / 'glyphs', masters=masters)\n",
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


def test_session_exit_clears_project_modules() -> None:
    """After session exit, sys.modules has no leftover project modules."""
    ns_before = {k for k in sys.modules if k.startswith("_tkproj_")}
    with open_project(LATIN_SANS) as session:
        ns = session._ns
        assert any(k == ns or k.startswith(ns + ".") for k in sys.modules)
        assert "system" in sys.modules
        assert "elements" in sys.modules
    for bare in ("system", "elements", "spacing", "font"):
        mod = sys.modules.get(bare)
        if mod is not None:
            f = getattr(mod, "__file__", "") or ""
            assert "latin_sans" not in f.replace("\\", "/")
    leftover = [k for k in sys.modules if k == ns or k.startswith(ns + ".")]
    assert leftover == [], leftover
    ns_after = {k for k in sys.modules if k.startswith("_tkproj_")}
    assert ns_after <= ns_before


def test_build_audit_diff_use_session() -> None:
    """Smoke: build / audit / diff entry points open a session (no purge)."""
    import typekernel.cli.load as load_mod
    from typekernel.cli.audit import audit_project
    from typekernel.cli.diff_cmd import project_glyph_hashes
    from typekernel.cli.load import build_font_from_project, load_project

    assert not hasattr(load_mod, "_purge_project_local_modules")

    project = load_project(LATIN_SANS)
    font = build_font_from_project(
        project, family_name="LatinSans", project_root=LATIN_SANS
    )
    assert "n" in font
    report = audit_project(LATIN_SANS, glyphs=["n", "o", "H", "O"])
    assert report.glyphs == 4
    hashes = project_glyph_hashes(LATIN_SANS)
    assert "n" in hashes
