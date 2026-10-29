"""Starters ship brief.md + quality disclaimer (P0 honesty)."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".agents/skills/typekernel-font-design/SKILL.md"
DISCLAIMER = "结构示例，字形未通过视觉评审，不要当作字形质量范本"


def test_latin_sans_tk_new_includes_brief(tmp_path: Path) -> None:
    root = create_project("with_brief", parent=tmp_path, starter="latin-sans")
    assert (root / "brief.md").is_file()
    text = (root / "brief.md").read_text(encoding="utf-8")
    assert DISCLAIMER in text


def test_three_starters_readme_disclaimer() -> None:
    for name in ("latin_sans", "latin_humanist_italic", "latin_chancery"):
        readme = ROOT / "src/typekernel/starters" / name / "README.md"
        assert readme.is_file(), name
        assert DISCLAIMER in readme.read_text(encoding="utf-8"), name


def test_skill_has_starter_quality_disclaimer() -> None:
    assert DISCLAIMER in SKILL.read_text(encoding="utf-8")
