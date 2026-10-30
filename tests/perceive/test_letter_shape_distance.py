"""S2 same-letter shape distance vs a reference session."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.perceive.voice import letter_shape_distance
from typekernel.project import open_project


def test_letter_shape_distance_self_near_zero(tmp_path: Path) -> None:
    root = create_project("voice_a", parent=tmp_path, starter="latin-sans")
    with open_project(root) as a, open_project(root) as b:
        d = letter_shape_distance(a, b, ord("o"))
    assert d == 0.0


def test_letter_shape_distance_missing_is_inf(tmp_path: Path) -> None:
    root = create_project("voice_b", parent=tmp_path, starter="latin-sans")
    with open_project(root) as session:
        d = letter_shape_distance(session, session, 0x01F600)  # no glyph
    assert d == float("inf")
