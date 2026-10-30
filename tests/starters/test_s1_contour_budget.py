"""S1 exit: control o ≤ 2 contours and ≤ 16 segments after tidy."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.project import open_project


def _o_budget(starter: str, tmp_path: Path) -> tuple[int, list[int]]:
    root = create_project(f"s1_{starter}", parent=tmp_path, starter=starter)
    with open_project(root) as session:
        g = session.evaluate("o")
        contours = g.drawing.outline().contours
        return len(contours), [len(c.segments) for c in contours]


def test_humanist_italic_o_budget(tmp_path: Path) -> None:
    n, segs = _o_budget("latin-humanist-italic", tmp_path)
    assert n <= 2, (n, segs)
    assert all(s <= 16 for s in segs), segs


def test_chancery_o_budget(tmp_path: Path) -> None:
    n, segs = _o_budget("latin-chancery", tmp_path)
    assert n <= 2, (n, segs)
    assert all(s <= 16 for s in segs), segs


def test_latin_sans_o_still_tight(tmp_path: Path) -> None:
    n, segs = _o_budget("latin-sans", tmp_path)
    assert n <= 2
    assert all(s <= 16 for s in segs), segs
