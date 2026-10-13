"""OpenType feature helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

from typekernel.compile import build_font
from typekernel.compile.features import add_standard_ligatures, standard_feature_text
from typekernel.font import Font
from typekernel.parts import Controls, DesignContext


def test_liga_glyphs_and_fea(tmp_path) -> None:
    ctx = DesignContext.code_clear()
    controls = Controls.from_context(ctx)
    font = Font.from_context(ctx, "Feat")
    font.add_chars(controls.build_all("fl"))
    add_standard_ligatures(font, controls.control_glyphs())
    font.features = standard_feature_text(case=False)
    build_font(font, tmp_path, formats=("otf",))
    assert "fi" in font and "fl" in font
    assert "feature liga" in font.features
