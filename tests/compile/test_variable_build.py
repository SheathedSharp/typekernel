"""build_variable_font: designed masters become one variable font."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

from typekernel.compile import build_variable_font, write_masters_designspace
from typekernel.font import Font, Master
from typekernel.parts import Controls, DesignContext


def _master(stem: float, style: str, wght: float) -> Master:
    ctx = DesignContext.code_clear()
    font = Font.from_context(ctx, "Var Sans", style, weight_class=int(wght))
    font.add_chars(Controls.from_context(ctx.tuned(stem=stem)).build_all())
    return Master({"wght": wght}, font)


@pytest.fixture
def masters() -> list[Master]:
    return [_master(86, "Regular", 400), _master(50, "Light", 200), _master(140, "Bold", 800)]


def test_designspace_layout(masters: list[Master], tmp_path: Path) -> None:
    ds_path, ufos = write_masters_designspace(masters, tmp_path)
    assert ds_path == tmp_path / "VarSans.designspace"
    assert [p.name for p in ufos] == [
        "VarSans-Regular.ufo",
        "VarSans-Light.ufo",
        "VarSans-Bold.ufo",
    ]
    doc = DesignSpaceDocument.fromfile(ds_path)
    (axis,) = doc.axes
    assert (axis.tag, axis.minimum, axis.default, axis.maximum) == ("wght", 200, 400, 800)
    assert [i.styleName for i in doc.instances] == ["Light", "Regular", "Bold"]
    assert doc.findDefault().styleName == "Regular"


def test_incompatible_masters_rejected(masters: list[Master], tmp_path: Path) -> None:
    masters[1].font.remove_glyph("q")
    with pytest.raises(ValueError, match="not compatible"):
        build_variable_font(masters, tmp_path)


def test_build_ttf_and_cff2(masters: list[Master], tmp_path: Path) -> None:
    result = build_variable_font(masters, tmp_path, formats=("ttf", "otf"))
    ttf = TTFont(result.binaries["ttf"])
    assert {"fvar", "gvar", "HVAR"} <= set(ttf.keys())
    assert "CFF2" in TTFont(result.binaries["otf"])
    (axis,) = ttf["fvar"].axes
    assert (axis.minValue, axis.defaultValue, axis.maxValue) == (200, 400, 800)
    names = [ttf["name"].getDebugName(i.subfamilyNameID) for i in ttf["fvar"].instances]
    assert names == ["Light", "Regular", "Bold"]
    assert (tmp_path / "VarSans-VF.ttf.manifest.json").is_file()


def test_wrong_start_point_is_caught(masters: list[Master], tmp_path: Path) -> None:
    from typekernel.font import Glyph
    from typekernel.geo.contour import Contour
    from typekernel.geo.outline import Outline

    bold = masters[2].font
    o = bold["o"]
    outer, counter = o.outline.contours
    rotated = Contour(outer.segments[1:] + outer.segments[:1], closed=True)
    bold.add_glyph(
        Glyph(o.name, Outline((rotated, counter)), o.advance, o.unicodes, o.anchors),
        replace=True,
    )
    from typekernel.font import check_masters

    assert check_masters(masters) == []  # segment kinds still line up
    with pytest.raises(ValueError, match="wrong_start_point"):
        build_variable_font(masters, tmp_path)


def test_clean_masters_have_no_structural_problems(masters: list[Master], tmp_path: Path) -> None:
    from typekernel.compile import deep_check_masters

    _, ufos = write_masters_designspace(masters, tmp_path)
    errors, _ = deep_check_masters(ufos, [m.style_name for m in masters])
    assert errors == []


@pytest.mark.parametrize(("wght", "index"), [(200, 1), (400, 0), (800, 2)])
def test_instances_reproduce_masters(
    masters: list[Master], tmp_path: Path, wght: int, index: int
) -> None:
    result = build_variable_font(masters, tmp_path)
    inst = instantiateVariableFont(TTFont(result.binaries["ttf"]), {"wght": wght})
    for name in ("n", "m", "o", "d"):
        assert inst["hmtx"][name][0] == round(masters[index].font[name].advance)
