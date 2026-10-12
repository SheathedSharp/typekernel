"""PNG specimen renderer (preview only)."""

from __future__ import annotations

from pathlib import Path

import pytest

PIL = pytest.importorskip("PIL")

from typekernel.geo.fixtures import load_synthetic_outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.qa.specimen_png import main, render_outline_png

FIXTURE = Path(__file__).parent.parent / "fixtures" / "synthetic_O.json"


def test_render_synthetic_o_png(tmp_path: Path) -> None:
    outline = load_synthetic_outline(FIXTURE)
    out = tmp_path / "O.png"
    result = render_outline_png(outline, out, size=256)
    assert result == out
    assert out.is_file()
    assert out.stat().st_size > 0
    # Sanity: PNG magic
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_render_rejects_non_positive_size(tmp_path: Path) -> None:
    builder = PathBuilder()
    builder.moveTo(0, 0)
    builder.lineTo(10, 0)
    builder.lineTo(10, 10)
    builder.closePath()
    with pytest.raises(ValueError, match="size"):
        render_outline_png(builder.build(), tmp_path / "x.png", size=0)


def test_cli_writes_specimen(tmp_path: Path) -> None:
    out = tmp_path / "cli_O.png"
    code = main(["--fixture", str(FIXTURE), "-o", str(out), "--size", "128"])
    assert code == 0
    assert out.is_file() and out.stat().st_size > 0
