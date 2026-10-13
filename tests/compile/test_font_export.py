"""Font → UFO: every glyph, cmap, metrics, kerning, anchors, components."""

from __future__ import annotations

from pathlib import Path

import pytest

ufoLib2 = pytest.importorskip("ufoLib2")

from typekernel.compile import font_to_ufo, write_font_to_ufo
from typekernel.font import Anchor, Component, Font, Glyph
from typekernel.geo.outline import Outline
from typekernel.parts import (
    ComposedGlyph,
    DesignContext,
    KernPair,
    KernTable,
    build_n,
    build_o,
    vertical_stem,
)


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.fixture
def font(ctx: DesignContext) -> Font:
    f = Font.from_context(ctx, "Export Sans")
    f.add_glyph(
        Glyph.for_char("n", build_n(ctx), anchors=(Anchor("top", 300.0, ctx.x_height),))
    )
    f.add_char("o", build_o(ctx))
    f.add_glyph(Glyph("o.alt", f["o"].outline, f["o"].advance))
    o_adv = f["o"].advance
    f.add_glyph(
        Glyph(
            "oo",
            Outline(()),
            2 * o_adv,
            components=(Component("o"), Component.offset("o", o_adv, 0)),
        )
    )
    f.add_kern_table(KernTable((KernPair("n", "o", -15.0),)))
    f.features = "languagesystem DFLT dflt;\n"
    return f


def test_font_to_ufo_writes_glyph_set(font: Font, ctx: DesignContext) -> None:
    ufo = font_to_ufo(font)
    assert ufo.lib["public.glyphOrder"] == [".notdef", "space", "n", "o", "o.alt", "oo"]
    assert ufo["n"].unicodes == [ord("n")]
    assert ufo["o.alt"].unicodes == []
    assert ufo["n"].width == pytest.approx(font["n"].advance)
    assert len(ufo["o"].contours) == 2
    assert [a.name for a in ufo["n"].anchors] == ["top"]
    assert [c.baseGlyph for c in ufo["oo"].components] == ["o", "o"]
    assert ufo.kerning[("n", "o")] == -15.0
    assert ufo.features.text.startswith("languagesystem")


def test_font_to_ufo_metrics_follow_context(font: Font, ctx: DesignContext) -> None:
    info = font_to_ufo(font).info
    assert info.unitsPerEm == 1000
    assert info.xHeight == round(ctx.x_height)
    assert info.capHeight == round(ctx.cap_height)
    assert info.openTypeOS2TypoAscender == round(ctx.ascender)
    assert info.openTypeOS2TypoDescender == round(ctx.descender)
    # o overshoots the baseline, so win descent must cover it
    assert info.openTypeOS2WinDescent >= -round(ctx.descender)
    assert info.openTypeOS2WinAscent >= round(ctx.ascender)
    assert info.postscriptBlueValues[:2] == [-round(ctx.overshoot), 0]


def test_win_metrics_cover_tall_ink(font: Font, ctx: DesignContext) -> None:
    stem = vertical_stem(ctx, 0, ctx.descender - 100, ctx.ascender + 150)
    tall = ComposedGlyph((stem,), (), 200.0, ctx)
    font.add_glyph(Glyph.from_composed("tall", tall))
    info = font_to_ufo(font).info
    assert info.openTypeOS2WinAscent >= round(ctx.ascender + 150)
    assert info.openTypeOS2WinDescent >= -round(ctx.descender - 100)


def test_invalid_font_is_rejected(font: Font) -> None:
    font.remove_glyph(".notdef")
    with pytest.raises(ValueError, match="missing .notdef"):
        font_to_ufo(font)


def test_write_font_to_ufo_roundtrip_and_overwrite(font: Font, tmp_path: Path) -> None:
    path = write_font_to_ufo(font, tmp_path / "Export.ufo")
    reopened = ufoLib2.Font.open(path)
    assert set(reopened.keys()) == {".notdef", "space", "n", "o", "o.alt", "oo"}
    with pytest.raises(FileExistsError):
        write_font_to_ufo(font, path)
    write_font_to_ufo(font, path, overwrite=True)
