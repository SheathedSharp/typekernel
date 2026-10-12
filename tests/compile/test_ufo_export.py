"""UFO export round-trip via ufoLib2."""

from __future__ import annotations

from pathlib import Path

import pytest

ufoLib2 = pytest.importorskip("ufoLib2")

from typekernel.compile.ufo_export import write_outline_to_ufo
from typekernel.geo.path_builder import PathBuilder


def _square_outline():
    builder = PathBuilder()
    builder.moveTo(0, 0)
    builder.lineTo(100, 0)
    builder.lineTo(100, 100)
    builder.lineTo(0, 100)
    builder.closePath()
    return builder.build()


def test_write_and_reload_single_glyph(tmp_path: Path) -> None:
    ufo_path = tmp_path / "Single.ufo"
    write_outline_to_ufo(_square_outline(), ufo_path, glyph_name="A")

    assert ufo_path.is_dir()
    font = ufoLib2.Font.open(ufo_path)
    assert font.info.unitsPerEm == 1000
    assert "A" in font
    glyph = font["A"]
    assert glyph.width == 600
    assert len(list(glyph)) == 1


def test_cubic_outline_survives_export(tmp_path: Path) -> None:
    builder = PathBuilder()
    builder.moveTo(10.5, 20.25)
    builder.curveTo(30.0, 40.0, 50.0, 60.0, 70.125, 80.5)
    builder.closePath()
    outline = builder.build()

    ufo_path = tmp_path / "Cubic.ufo"
    write_outline_to_ufo(outline, ufo_path, glyph_name="C")
    font = ufoLib2.Font.open(ufo_path)
    points = [(p.x, p.y, p.type) for contour in font["C"] for p in contour]
    # Off-curve controls keep type None; on-curve curve endpoint present.
    assert (30.0, 40.0, None) in points
    assert (50.0, 60.0, None) in points
    assert any(p[0] == 70.125 and p[1] == 80.5 and p[2] == "curve" for p in points)
