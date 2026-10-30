"""script-roundhand starter smoke."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.diagnose.engine import audit_project
from typekernel.project import open_project


def test_script_roundhand_builds_and_audits_quiet(tmp_path: Path) -> None:
    root = create_project("rh", parent=tmp_path, starter="script-roundhand")
    with open_project(root) as session:
        for name in ("n", "o", "a", "e"):
            draft = session.evaluate(name)
            assert draft.drawing.outline().contours
            assert draft.skeleton is not None
        assert session.project.brief is not None
        assert session.project.brief.intent.tool == "pointed"
        assert session.project.brief.intent.genre == "roundhand"
    report = audit_project(root)
    assert report.errors == []
    assert report.warnings == []
