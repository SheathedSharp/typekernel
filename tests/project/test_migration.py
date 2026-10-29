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
