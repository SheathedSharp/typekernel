"""UFO export overwrite behaviour."""

from __future__ import annotations

from pathlib import Path

import pytest

ufoLib2 = pytest.importorskip("ufoLib2")

from typekernel.compile.ufo_export import write_outline_to_ufo
from typekernel.geo.path_builder import PathBuilder


def _square():
    b = PathBuilder()
    b.moveTo(0, 0)
    b.lineTo(10, 0)
    b.lineTo(10, 10)
    b.closePath()
    return b.build()


def test_overwrite_false_raises(tmp_path: Path) -> None:
    ufo = tmp_path / "G.ufo"
    write_outline_to_ufo(_square(), ufo, glyph_name="A")
    with pytest.raises(FileExistsError):
        write_outline_to_ufo(_square(), ufo, glyph_name="A")


def test_overwrite_true_replaces(tmp_path: Path) -> None:
    ufo = tmp_path / "G.ufo"
    write_outline_to_ufo(_square(), ufo, glyph_name="A")
    write_outline_to_ufo(_square(), ufo, glyph_name="B", overwrite=True)
    font = ufoLib2.Font.open(ufo)
    assert "B" in font
    assert "A" not in font
