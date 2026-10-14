"""Designed italic + weight variable font."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

from fontTools.ttLib import TTFont

from typekernel.compile import build_variable_font
from typekernel.font import Font, Master
from typekernel.parts import Controls, DesignContext
from typekernel.parts.italic import italic_design, vf_upright_controls


def _font(controls: Controls, style: str, *, stem: float | None = None) -> Font:
    ctx = controls.context
    if stem is not None:
        ctx = ctx.tuned(stem=stem)
    sheet = replace(controls, context=ctx)
    if stem is not None and stem >= 100:
        sheet = sheet.with_stem_relief()
    drawn = sheet.build_all()
    font = Font.from_context(ctx, "Ital VF", style)
    font.add_chars(drawn)
    return font


def test_wght_ital_masters_interpolate() -> None:
    from typekernel.font import check_masters

    base = DesignContext.code_clear()
    reg = vf_upright_controls(Controls.from_context(base))
    ital = italic_design(reg)
    bold = vf_upright_controls(
        Controls.from_context(base.tuned(stem=120.0)).with_stem_relief()
    )

    masters = [
        Master({"wght": 400, "ital": 0}, _font(reg, "Regular")),
        Master({"wght": 400, "ital": 1}, _font(ital, "Italic")),
        Master({"wght": 700, "ital": 0}, _font(bold, "Bold", stem=120.0)),
    ]
    assert check_masters(masters) == []


def test_wght_ital_masters_deep_check(tmp_path: Path) -> None:
    from typekernel.compile import deep_check_masters, write_masters_designspace

    base = DesignContext.code_clear()
    reg = vf_upright_controls(Controls.from_context(base))
    ital = italic_design(reg)
    bold = vf_upright_controls(
        Controls.from_context(base.tuned(stem=120.0)).with_stem_relief()
    )
    masters = [
        Master({"wght": 400, "ital": 0}, _font(reg, "Regular")),
        Master({"wght": 400, "ital": 1}, _font(ital, "Italic")),
        Master({"wght": 700, "ital": 0}, _font(bold, "Bold", stem=120.0)),
    ]
    _, ufos = write_masters_designspace(masters, tmp_path)
    errors, _ = deep_check_masters(ufos, [m.style_name for m in masters])
    assert errors == []


def test_wght_ital_vf_builds(tmp_path: Path) -> None:
    base = DesignContext.code_clear()
    reg = vf_upright_controls(Controls.from_context(base))
    masters = [
        Master({"wght": 400, "ital": 0}, _font(reg, "Regular")),
        Master({"wght": 400, "ital": 1}, _font(italic_design(reg), "Italic")),
        Master({"wght": 700, "ital": 0}, _font(reg, "Bold", stem=120.0)),
    ]
    result = build_variable_font(masters, tmp_path, formats=("ttf",))
    ttf = TTFont(result.binaries["ttf"])
    tags = {a.axisTag for a in ttf["fvar"].axes}
    assert tags == {"wght", "ital"}
