"""Glyph binding: names, code points, winding, standard glyphs."""

from __future__ import annotations

import pytest

from typekernel.font import (
    Anchor,
    Component,
    Glyph,
    glyph_name_for_char,
    normalize_winding,
    notdef_glyph,
    space_glyph,
)
from typekernel.geo.contour import signed_area
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts import ComposedGlyph, DesignContext, bowl, build_n


def _square(x0: float, y0: float, x1: float, y1: float) -> Outline:
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    return b.build()


def _areas(outline: Outline) -> list[float]:
    return [signed_area(c) for c in outline.contours]


@pytest.mark.parametrize(
    ("char", "name"),
    [("a", "a"), (",", "comma"), ("é", "eacute"), ("中", "uni4E2D"), ("😀", "u1F600")],
)
def test_glyph_name_for_char(char: str, name: str) -> None:
    assert glyph_name_for_char(char) == name


def test_glyph_name_for_char_rejects_strings() -> None:
    with pytest.raises(ValueError):
        glyph_name_for_char("ab")


def test_normalize_winding_orients_by_nesting() -> None:
    outer = _square(0, 0, 100, 100).contours[0]
    inner = _square(20, 20, 80, 80).contours[0]
    assert signed_area(outer) > 0 and signed_area(inner) > 0

    fixed = normalize_winding(Outline((outer, inner)))
    a_outer, a_inner = _areas(fixed)
    assert a_outer > 0
    assert a_inner < 0

    flipped = normalize_winding(Outline((outer, inner)), invert=True)
    assert [a > 0 for a in _areas(flipped)] == [False, True]


def test_from_composed_reverses_unsubtracted_holes() -> None:
    ctx = DesignContext.code_clear()
    outer, hole = bowl(ctx, 200, 260, rx=200, ry=270, thickness=ctx.stem)
    assert signed_area(outer.contours[0]) > 0 and signed_area(hole.contours[0]) > 0
    composed = ComposedGlyph((outer,), (hole,), 500.0, ctx)

    glyph = Glyph.from_composed("o", composed)
    a_outer, a_hole = _areas(glyph.outline)
    assert a_outer > 0
    assert a_hole < 0
    assert glyph.advance == 500.0


def test_from_composed_keeps_separate_solids_positive() -> None:
    ctx = DesignContext.code_clear()
    overlapping = ComposedGlyph(
        (_square(0, 0, 100, 100), _square(50, 50, 150, 150)), (), 200.0, ctx
    )
    glyph = Glyph.from_composed("x", overlapping)
    assert all(a > 0 for a in _areas(glyph.outline))


def test_for_char_names_and_maps() -> None:
    ctx = DesignContext.code_clear()
    n = build_n(ctx)
    glyph = Glyph.for_char(
        "n",
        n,
        anchors=(Anchor("top", 300, 600),),
        components=(Component.offset("dotaccent", 10, 20),),
    )
    assert glyph.name == "n"
    assert glyph.unicodes == (ord("n"),)
    assert glyph.advance == n.advance
    assert glyph.anchors[0].name == "top"
    assert glyph.components[0].transform == (1.0, 0.0, 0.0, 1.0, 10, 20)


def test_glyph_rejects_bad_identity() -> None:
    empty = Outline(())
    with pytest.raises(ValueError):
        Glyph("", empty, 0.0)
    with pytest.raises(ValueError):
        Glyph("a", empty, 0.0, unicodes=(97, 97))


def test_notdef_is_hollow_box() -> None:
    ctx = DesignContext.code_clear()
    g = notdef_glyph(ctx)
    assert g.name == ".notdef"
    assert g.unicodes == ()
    a_outer, a_inner = _areas(g.outline)
    assert a_outer > 0 > a_inner
    assert g.advance > 0


def test_space_glyph() -> None:
    ctx = DesignContext.code_clear()
    assert space_glyph(ctx).advance == pytest.approx(0.5 * ctx.x_height)
    g = space_glyph(ctx, 240)
    assert (g.name, g.unicodes, g.advance, g.outline.contour_count) == ("space", (32,), 240, 0)
