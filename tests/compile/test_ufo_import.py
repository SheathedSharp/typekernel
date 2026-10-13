"""UFO round-trip read."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

from typekernel.compile import build_font, read_font_from_ufo
from typekernel.font import Font
from typekernel.parts import Controls, DesignContext


def test_read_font_from_ufo_roundtrip(tmp_path: Path) -> None:
    ctx = DesignContext.code_clear()
    controls = Controls.from_context(ctx)
    font = Font.from_context(ctx, "Roundtrip")
    font.add_chars(controls.build_all("no"))
    build_font(font, tmp_path)
    ufo = tmp_path / "Roundtrip-Regular.ufo"
    back = read_font_from_ufo(ufo)
    assert back.info.family_name == "Roundtrip"
    assert "n" in back
