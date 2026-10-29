"""latin-chancery starter — control glyphs + flourish/pen_dot helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.cli.build import build_project
from typekernel.cli.load import load_project
from typekernel.cli.new import create_project
from typekernel.project import open_project

STARTER = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "typekernel"
    / "starters"
    / "latin_chancery"
)


def test_starter_tree_has_control_and_helpers() -> None:
    assert (STARTER / "system.py").is_file()
    assert (STARTER / "elements.py").is_file()
    assert (STARTER / "project.py").is_file()
    assert (STARTER / "spacing.py").is_file()
    assert (STARTER / "brief.md").is_file()
    elements = (STARTER / "elements.py").read_text(encoding="utf-8")
    assert "pen_dot" in elements
    assert "flourish_exit" in elements
    assert "anatomy.pen" in elements or "expand_skeleton" in elements
    for rel in (
        "glyphs/lower/n.py",
        "glyphs/lower/o.py",
        "glyphs/lower/h.py",
        "glyphs/lower/i.py",
        "glyphs/upper/H.py",
        "glyphs/upper/O.py",
    ):
        assert (STARTER / rel).is_file()


def test_system_uses_first_class_slant() -> None:
    project = load_project(STARTER)
    assert project.system.is_italic
    assert project.system.slant > 0
    assert "slant" not in project.system.tokens


def test_discover_evaluate_control_set() -> None:
    with open_project(STARTER) as session:
        assert {"n", "o", "H", "O", "h", "i"} <= set(session.specs())
        for name in ("n", "o", "H", "O", "h", "i"):
            drawing = session.evaluate(name).drawing
            assert len(drawing.contours) >= 1
            assert drawing.roles[0] == "ink"



def test_pen_dot_is_solid_not_a_ring() -> None:
    """A stroked closed circle would be ink+counter; a period must be one ink."""
    with open_project(STARTER) as session:
        period = session.evaluate("period").drawing
        assert len(period.contours) == 1
        assert period.roles == ("ink",)

        tittle = session.evaluate("i").drawing
        assert "counter" not in tittle.roles


def test_tk_new_chancery_builds_otf(tmp_path: Path) -> None:
    pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    root = create_project("demo_ch", parent=tmp_path, starter="latin-chancery")
    assert (root / "elements.py").is_file()
    assert "pen_dot" in (root / "elements.py").read_text(encoding="utf-8")
    font, result = build_project(root, out_dir=root / "build", formats=("otf",))
    names = {g.name for g in font}
    assert {"n", "o", "H", "O", ".notdef", "space"} <= names
    assert font["space"].advance > 0
    otf = result.binaries["otf"]
    assert otf.is_file()


def test_space_advance_from_tokens() -> None:
    """space_stem_mul / space_lsb_mul live on System.tokens, not hardcoded-only."""
    from typekernel.starters.latin_chancery.system import system as sys_

    assert "space_stem_mul" in sys_.tokens
    assert "space_lsb_mul" in sys_.tokens


def test_interpolation_g_class_clean() -> None:
    """P5-4: InterpolationCheck stays at 0 for the full chancery charset."""
    from typekernel.diagnose.checks.interpolation import InterpolationCheck
    from typekernel.diagnose.engine import CheckContext

    with open_project(STARTER) as session:
        ctx = CheckContext(session=session, project=session.project, system=session.project.system)
        findings = list(InterpolationCheck().run(ctx))
        assert findings == [], [getattr(f, "glyph", None) for f in findings]
