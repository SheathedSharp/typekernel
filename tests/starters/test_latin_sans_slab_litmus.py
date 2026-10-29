"""latin-sans with corners={"*": slab()} must build (P0 curve-neighbor fix)."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.audit import audit_project
from typekernel.cli.build import build_project
from typekernel.cli.new import create_project
from typekernel.project import open_project


def test_latin_sans_all_corners_slab_builds(tmp_path: Path) -> None:
    root = create_project("slab_litmus", parent=tmp_path, starter="latin-sans")
    project_py = root / "project.py"
    text = project_py.read_text(encoding="utf-8")
    text = text.replace(
        "from typekernel.plugins.corners import plain",
        "from typekernel.plugins.corners import slab",
    )
    text = text.replace('corners={"*": plain()}', 'corners={"*": slab()}')
    project_py.write_text(text, encoding="utf-8")

    with open_project(root) as session:
        for name in session.specs():
            session.evaluate(name)  # must not raise SlotFillError / ContinuityError

    _font, result = build_project(root, formats=("otf",))
    assert result.binaries.get("otf")
    report = audit_project(root)
    assert report.errors == []
