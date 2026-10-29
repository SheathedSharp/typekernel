"""latin-sans litmus: slab / bracketed / rounded corners all build."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.cli.audit import audit_project
from typekernel.cli.build import build_project
from typekernel.cli.new import create_project
from typekernel.project import open_project

_CONFIGS = [
    ("slab", "from typekernel.plugins.corners import slab", 'corners={"*": slab()}'),
    (
        "bracketed",
        "from typekernel.plugins.corners import bracketed",
        'corners={"*": bracketed()}',
    ),
    (
        "rounded",
        "from typekernel.plugins.corners import rounded",
        'corners={"*": rounded(radius=0.35)}',
    ),
]


@pytest.mark.parametrize("label,import_line,corners_line", _CONFIGS, ids=[c[0] for c in _CONFIGS])
def test_latin_sans_corner_style_builds(
    tmp_path: Path, label: str, import_line: str, corners_line: str
) -> None:
    root = create_project(f"litmus_{label}", parent=tmp_path, starter="latin-sans")
    project_py = root / "project.py"
    text = project_py.read_text(encoding="utf-8")
    text = text.replace("from typekernel.plugins.corners import plain", import_line)
    text = text.replace('corners={"*": plain()}', corners_line)
    project_py.write_text(text, encoding="utf-8")

    with open_project(root) as session:
        # Focus on anatomy-rewritten controls + a few straight glyphs that have corner slots.
        for name in ("n", "h", "i", "l", "H", "o", "O"):
            session.evaluate(name)

    _font, result = build_project(root, formats=("otf",))
    assert result.binaries.get("otf"), label
    report = audit_project(root, glyphs=["n", "h", "i", "l", "H", "o", "O"])
    assert report.errors == [], (label, [f.message for f in report.errors])
