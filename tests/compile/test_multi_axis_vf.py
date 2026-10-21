"""Two-axis variable font build."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

from fontTools.ttLib import TTFont

from typekernel.compile import build_variable_font
from typekernel.font import Font, Master
from typekernel.parts import DesignContext, FormSources


def _font(stem: float, wdth: float, style: str) -> Font:
    scale = wdth / 100.0
    ctx = DesignContext.code_clear().tuned(stem=stem)
    sheet = FormSources.from_context(ctx).with_stem_relief()
    if scale != 1.0:
        sheet = sheet.tuned_n(counter=sheet.n.counter * scale).tuned_o(rx=sheet.o.rx * scale)
    drawn = sheet.derive("no")
    font = Font.from_context(ctx, "Two Axis", style)
    font.add_chars(drawn)
    return font


def test_build_wght_wdth_vf(tmp_path: Path) -> None:
    masters = [
        Master({"wght": 400, "wdth": 100}, _font(86, 100, "Regular")),
        Master({"wght": 400, "wdth": 125}, _font(86, 125, "Wide")),
        Master({"wght": 700, "wdth": 100}, _font(120, 100, "Bold")),
    ]
    result = build_variable_font(masters, tmp_path, formats=("ttf",))
    ttf = TTFont(result.binaries["ttf"])
    tags = {a.axisTag for a in ttf["fvar"].axes}
    assert tags == {"wght", "wdth"}
