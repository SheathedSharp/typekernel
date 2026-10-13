"""build_font: a Font becomes installable OTF + TTF binaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

from fontTools.ttLib import TTFont

from typekernel.compile import build_font
from typekernel.font import Anchor, Font, Glyph
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts import (
    DesignContext,
    auto_class_kern,
    build_h,
    build_n,
    build_o,
    default_latin_kern_classes,
)


def _acute_mark(ctx: DesignContext) -> Glyph:
    b = PathBuilder()
    b.moveTo(-30, ctx.x_height + 40)
    b.lineTo(30, ctx.x_height + 40)
    b.lineTo(60, ctx.x_height + 140)
    b.lineTo(10, ctx.x_height + 140)
    b.closePath()
    return Glyph(
        "acutecomb",
        b.build(),
        0.0,
        unicodes=(0x0301,),
        anchors=(Anchor("_top", 0.0, ctx.x_height),),
    )


@pytest.fixture
def font() -> Font:
    ctx = DesignContext.code_clear()
    f = Font.from_context(ctx, "Build Sans", "Regular")
    glyphs = {"n": build_n(ctx), "o": build_o(ctx), "h": build_h(ctx)}
    for ch, g in glyphs.items():
        f.add_glyph(Glyph.for_char(ch, g, anchors=(Anchor("top", g.advance / 2, ctx.x_height),)))
    f.add_glyph(_acute_mark(ctx))
    f.add_class_kern_table(auto_class_kern(glyphs, default_latin_kern_classes()))
    return f


def _feature_tags(tt: TTFont) -> set[str]:
    return {fr.FeatureTag for fr in tt["GPOS"].table.FeatureList.FeatureRecord}


def test_build_font_produces_otf_and_ttf(font: Font, tmp_path: Path) -> None:
    result = build_font(font, tmp_path)
    assert result.ufo == tmp_path / "BuildSans-Regular.ufo"
    assert set(result.binaries) == {"otf", "ttf"}

    otf = TTFont(result.binaries["otf"])
    ttf = TTFont(result.binaries["ttf"])
    assert "CFF " in otf and "glyf" in ttf

    for tt in (otf, ttf):
        assert tt.getGlyphOrder() == [".notdef", "space", "n", "o", "h", "acutecomb"]
        cmap = tt.getBestCmap()
        assert cmap[ord("n")] == "n" and cmap[0x20] == "space" and cmap[0x0301] == "acutecomb"
        assert tt["hmtx"]["n"][0] == round(font["n"].advance)
        assert tt["OS/2"].sTypoAscender == round(font.info.ascender)
        assert tt["OS/2"].fsSelection & (1 << 7)
        assert tt["name"].getDebugName(1) == "Build Sans"
        tags = _feature_tags(tt)
        assert "kern" in tags
        assert "mark" in tags


def test_build_font_writes_manifests_and_rebuilds(font: Font, tmp_path: Path) -> None:
    build_font(font, tmp_path, formats=("ttf",))
    result = build_font(font, tmp_path, formats=("ttf",))
    assert set(result.binaries) == {"ttf"}
    data = json.loads((tmp_path / "BuildSans-Regular.ttf.manifest.json").read_text())
    assert data["output_format"] == "ttf"
    assert data["filters"] == []


def test_build_font_rejects_unknown_format(font: Font, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="output_format"):
        build_font(font, tmp_path, formats=("woff",))  # type: ignore[arg-type]
