"""latin-sans with corners={"*": slab()} must build (P0 curve-neighbor fix)."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.audit import audit_project
from typekernel.cli.build import build_project
from typekernel.cli.load import load_project
from typekernel.cli.new import create_project


def test_latin_sans_all_corners_slab_builds(tmp_path: Path) -> None:
    root = create_project("slab_litmus", parent=tmp_path, starter="latin-sans")
    font_py = root / "font.py"
    text = font_py.read_text(encoding="utf-8")
    text = text.replace(
        "from typekernel.plugins.corners import plain",
        "from typekernel.plugins.corners import slab",
    )
    text = text.replace('corners={"*": plain()}', 'corners={"*": slab()}')
    font_py.write_text(text, encoding="utf-8")

    project = load_project(root)
    project.discover()
    for name in project.specs():
        project.evaluate(name)  # must not raise SlotFillError / ContinuityError

    _font, result = build_project(root, formats=("otf",))
    assert result.binaries.get("otf")
    report = audit_project(root)
    assert report.errors == []
