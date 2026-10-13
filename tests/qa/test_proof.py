"""Proof sheets from compiled binaries."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")
pytest.importorskip("PIL")

from typekernel.compile import build_font
from typekernel.font import Font, Glyph
from typekernel.parts import Controls, DesignContext
from typekernel.qa.proof import (
    proof_charset_grid,
    proof_context,
    proof_kern_pairs,
    proof_sheet,
    proof_spacing_strings,
)


@pytest.fixture
def otf_path(tmp_path: Path) -> Path:
    ctx = DesignContext.code_clear()
    controls = Controls.from_context(ctx)
    drawn = controls.build_all("no")
    font = Font.from_context(ctx, "Proof Test")
    for ch, g in drawn.items():
        font.add_glyph(Glyph.for_char(ch, g))
    result = build_font(font, tmp_path, formats=("otf",))
    return result.binaries["otf"]


def test_proof_context_writes_png(otf_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "ctx.png"
    proof_context(otf_path, "hello world", out, size=24)
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_proof_spacing_and_kern(otf_path: Path, tmp_path: Path) -> None:
    proof_spacing_strings(otf_path, tmp_path / "sp.png")
    proof_kern_pairs(otf_path, tmp_path / "kern.png", pairs=(("n", "o"),))
    assert (tmp_path / "sp.png").stat().st_size > 0


def test_proof_sheet_and_grid(otf_path: Path, tmp_path: Path) -> None:
    proof_charset_grid(otf_path, tmp_path / "grid.png")
    proof_sheet(
        otf_path,
        tmp_path / "sheet.png",
        context_text="The quick brown fox",
        include_grid=False,
    )
    assert (tmp_path / "sheet.png").stat().st_size > 0
