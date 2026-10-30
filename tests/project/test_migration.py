"""Legacy conventions raise MigrationError with old→new field map."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.project import MigrationError, open_project


def test_legacy_font_get_project_raises_migration_error(tmp_path: Path) -> None:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "glyphs").mkdir()
    (root / "system.py").write_text(
        "FAMILY_NAME = \"Legacy\"\nSTYLE_NAME = \"Regular\"\n",
        encoding="utf-8",
    )
    (root / "font.py").write_text(
        "def get_project():\n    raise RuntimeError(\"should not load\")\n",
        encoding="utf-8",
    )
    with pytest.raises(MigrationError) as ei, open_project(root):
        pass
    assert "project.py → PROJECT" in str(ei.value)
    assert "font.get_project / font.project" in ei.value.mapping
    assert "FAMILY_NAME / STYLE_NAME" in ei.value.mapping


def test_legacy_names_on_system_with_project_raise(tmp_path: Path) -> None:
    """PROJECT present but system.py still exports legacy names → MigrationError."""
    root = tmp_path / "half_migrated"
    root.mkdir()
    (root / "glyphs").mkdir()
    (root / "system.py").write_text(
        "from typekernel.system import Overshoot, System, Zones\n"
        "system = System(\n"
        "    upm=1000,\n"
        "    zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),\n"
        "    overshoot=Overshoot(round=12, pointed=10),\n"
        '    stem={"lc": 80},\n'
        ")\n"
        'FAMILY_NAME = "Half"\n'
        "AUDIT_STEMS = {}\n",
        encoding="utf-8",
    )
    (root / "project.py").write_text(
        "from system import system\n"
        "from typekernel.project import FamilyInfo, Project\n"
        "PROJECT = Project(info=FamilyInfo(family='Half'), system=system)\n",
        encoding="utf-8",
    )
    with pytest.raises(MigrationError) as ei, open_project(root):
        pass
    msg = str(ei.value)
    assert "FAMILY_NAME" in msg
    assert "AUDIT_STEMS" in msg
    assert "project.py → PROJECT" in msg
