"""Composite glyphs: base + mark components and anchor alignment."""

from __future__ import annotations

from typekernel.font import Anchor, Font, Glyph
from typekernel.parts import DesignContext, build_n, build_o
from typekernel.parts.diacritics import add_composite_latin
from typekernel.parts.marks import acute_comb


def test_add_composite_aligns_mark_to_base_top() -> None:
    ctx = DesignContext.code_clear()
    n, o = build_n(ctx), build_o(ctx)
    font = Font.from_context(ctx, "Composite Test")
    font.add_glyph(
        Glyph.from_composed("a", n, anchors=(Anchor("top", n.advance / 2, ctx.x_height),))
    )
    font.add_glyph(Glyph.from_composed("acutecomb", acute_comb(n, o, ctx), unicodes=(0x0301,)))
    font.add_composite("á", "a", (("acutecomb", "top", "_top"),))
    g = font["aacute"]
    assert g.advance == font["a"].advance
    assert len(g.components) == 2
    mark = g.components[1]
    assert mark.base == "acutecomb"
    assert mark.transform[4] != 0.0 or mark.transform[5] != 0.0


def test_add_composite_latin_registers_cedilla() -> None:
    ctx = DesignContext.code_clear()
    font = Font.from_context(ctx, "Latin")
    from typekernel.parts import Controls

    controls = Controls.from_context(ctx)
    font.add_chars(controls.build_all())
    add_composite_latin(font, controls.control_glyphs())
    assert "ccedilla" in font
    assert font.cmap()[ord("ç")] == "ccedilla"
