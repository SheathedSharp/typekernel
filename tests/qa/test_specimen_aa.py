"""Anti-aliased specimen renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

PIL = pytest.importorskip("PIL")
from PIL import Image

from typekernel.geo.path_builder import PathBuilder
from typekernel.qa.specimen_png import render_outline_png


def test_supersample_produces_soft_rgb_edges(tmp_path: Path) -> None:
    b = PathBuilder()
    b.addEllipse(0, 0, 100, 80)
    out = tmp_path / "aa.png"
    render_outline_png(b.build(), out, size=128, supersample=4)
    img = Image.open(out).convert("RGB")
    # Soft edges blend ink into the background → intermediate channel values.
    soft = False
    pixels = img.load()
    assert pixels is not None
    for y in range(img.height):
        for x in range(img.width):
            px = pixels[x, y]
            if any(60 < c < 220 for c in px):
                soft = True
                break
        if soft:
            break
    assert soft, "expected anti-aliased intermediate RGB values"


def test_supersample_rejects_non_positive(tmp_path: Path) -> None:
    b = PathBuilder()
    b.addEllipse(0, 0, 10, 10)
    with pytest.raises(ValueError, match="supersample"):
        render_outline_png(b.build(), tmp_path / "x.png", supersample=0)
