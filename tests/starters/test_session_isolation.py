"""ProjectSession isolation across real starters (letter glyphs allowed here)."""

from __future__ import annotations

import sys
from pathlib import Path

from typekernel.cli.audit import audit_project
from typekernel.cli.diff_cmd import project_glyph_hashes
from typekernel.cli.load import build_font_from_project, load_project
from typekernel.project import open_project
from typekernel.qa.outline_hash import outline_hash

LATIN_SANS = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
HUMANIST = (
    Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_humanist_italic"
)


def test_alternate_projects_stable_distinct_hashes() -> None:
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


def test_session_exit_clears_project_modules() -> None:
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
    import typekernel.cli.load as load_mod

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
