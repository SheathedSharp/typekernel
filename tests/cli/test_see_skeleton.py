"""tk see --skeleton."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.cli.see_cmd import see_project


def test_see_skeleton_roundhand(tmp_path: Path) -> None:
    root = create_project("skel", parent=tmp_path, starter="script-roundhand")
    paths = see_project(root, "n", out_dir=tmp_path / "see", skeleton=True)
    assert any("skeleton" in p.name for p in paths)
    assert any(p.is_file() for p in paths if "skeleton" in p.name)
