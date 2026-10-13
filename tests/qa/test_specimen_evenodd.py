"""Preview fill: counters punch out, separate ink fills, regardless of winding."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PIL")

from PIL import Image

from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.qa.specimen_png import render_outline_png


def _square(b: PathBuilder, x0: float, y0: float, x1: float, y1: float) -> None:
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()


def _dark(path: Path, xy: tuple[int, int]) -> bool:
    return Image.open(path).convert("L").getpixel(xy) < 128


def test_separate_ink_fills_and_counter_punches(tmp_path: Path) -> None:
    b = PathBuilder()
    _square(b, 0, 0, 100, 100)  # stem
    _square(b, 30, 30, 70, 70)  # counter, same winding on purpose
    _square(b, 0, 200, 100, 300)  # tittle above
    out = render_outline_png(Outline(b.build().contours), tmp_path / "evenodd.png", size=300)
    # outline spans y 0..300 → image rows flip; sample pixel centres
    size, margin = 300, 300 * 0.08
    scale = (size - 2 * margin) / 300

    def px(x: float, y: float) -> tuple[int, int]:
        offset_x = margin + ((size - 2 * margin) - 100 * scale) / 2
        return int(offset_x + x * scale), int(margin + (300 - y) * scale)

    assert _dark(out, px(10, 10))  # stem ink
    assert not _dark(out, px(50, 50))  # counter
    assert _dark(out, px(50, 250))  # tittle ink
    assert not _dark(out, px(50, 150))  # gap between
