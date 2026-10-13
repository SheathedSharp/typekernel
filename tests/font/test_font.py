"""Font container: glyph set, cmap, kerning groups, validation."""

from __future__ import annotations

import pytest

from typekernel.font import Component, Font, FontInfo, Glyph
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.parts import (
    ClassKernPair,
    ClassKernTable,
    DesignContext,
    KernClass,
    KernPair,
    KernTable,
    build_n,
    build_o,
)


@pytest.fixture
def ctx() -> DesignContext:
    return DesignContext.code_clear()


@pytest.fixture
def font(ctx: DesignContext) -> Font:
    f = Font.from_context(ctx, "Test Sans")
    f.add_chars({"n": build_n(ctx), "o": build_o(ctx)})
    return f


def test_from_context_seeds_standard_glyphs(ctx: DesignContext) -> None:
    f = Font.from_context(ctx, "Test Sans", space_width=200)
    assert f.glyph_order == [".notdef", "space"]
    assert f["space"].advance == 200
    assert f.context is ctx
    assert f.validate() == []


def test_notdef_exported_first_regardless_of_insertion(ctx: DesignContext) -> None:
    from typekernel.font import notdef_glyph

    f = Font(info=FontInfo(family_name="X"))
    f.add_char("n", build_n(ctx))
    f.add_glyph(notdef_glyph(ctx))
    assert f.glyph_order == [".notdef", "n"]


def test_add_glyph_clash_and_replace(font: Font, ctx: DesignContext) -> None:
    with pytest.raises(ValueError, match="already exists"):
        font.add_char("n", build_n(ctx))
    wider = build_n(ctx.tuned(stem=120))
    font.add_char("n", wider, replace=True)
    assert font["n"].advance == wider.advance
    assert len(font) == 4


def test_cmap_and_resolve(font: Font) -> None:
    assert font.cmap() == {0x20: "space", ord("n"): "n", ord("o"): "o"}
    assert font.resolve("o") == "o"
    assert font.resolve(" ") == "space"
    assert font.resolve("space") == "space"
    assert font.resolve("z") is None
    assert "n" in font and "z" not in font


def test_add_kern_table_resolves_and_skips(font: Font) -> None:
    table = KernTable((KernPair("n", "o", -12.0), KernPair("o", "z", -5.0)))
    skipped = font.add_kern_table(table)
    assert font.kerning == {("n", "o"): -12.0}
    assert skipped == ["z"]
    with pytest.raises(KeyError):
        font.add_kern_table(table, strict=True)


def test_add_class_kern_table_writes_ufo_groups(font: Font) -> None:
    table = ClassKernTable(
        classes=(KernClass("round", ("o", "c")), KernClass("straight", ("n", "h"))),
        pairs=(
            ClassKernPair("round", "straight", -7.0),
            ClassKernPair("straight", "round", -9.0),
        ),
    )
    skipped = font.add_class_kern_table(table)
    assert skipped == ["c", "h"]
    assert font.groups["public.kern1.round"] == ("o",)
    assert font.groups["public.kern2.straight"] == ("n",)
    assert font.kerning[("public.kern1.round", "public.kern2.straight")] == -7.0
    assert font.kerning[("public.kern1.straight", "public.kern2.round")] == -9.0
    assert font.validate() == []


def test_class_kern_overlap_rejected(font: Font) -> None:
    table = ClassKernTable(classes=(KernClass("a", ("n",)), KernClass("b", ("n", "o"))))
    with pytest.raises(ValueError, match="two kerning groups"):
        font.add_class_kern_table(table)


def test_validate_reports_problems(font: Font) -> None:
    empty = Outline(())
    font.add_glyph(Glyph("dup", empty, 100, unicodes=(ord("n"),)))
    font.add_glyph(Glyph("broken", empty, 100, components=(Component("nope"),)))
    font.add_glyph(Glyph("loopA", empty, 100, components=(Component("loopB"),)))
    font.add_glyph(Glyph("loopB", empty, 100, components=(Component("loopA"),)))
    open_c = Contour((LineSegment(Point(0, 0), Point(10, 10)),), closed=False)
    font.add_glyph(Glyph("open", Outline((open_c,)), 100))
    font.add_glyph(Glyph("neg", empty, -1))
    font.kerning[("n", "ghost")] = -3.0
    font.remove_glyph(".notdef")

    text = "\n".join(font.validate())
    assert "missing .notdef" in text
    assert "U+006E" in text
    assert "missing component 'nope'" in text
    assert "component cycle" in text
    assert "contour 0 is open" in text
    assert "negative advance" in text
    assert "unknown 'ghost'" in text
