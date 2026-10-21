"""check_masters catches what would stop masters from interpolating."""

from __future__ import annotations

import pytest

from typekernel.font import Font, Glyph, Master, axis_ranges, check_masters
from typekernel.geo.outline import Outline
from typekernel.parts import ClassKernTable, DesignContext, FormSources, KernClass


def _font(stem: float, style: str, family: str = "M Sans") -> Font:
    ctx = DesignContext.code_clear()
    f = Font.from_context(ctx, family, style)
    f.add_chars(FormSources.from_context(ctx.tuned(stem=stem)).derive("nohb"))
    return f


@pytest.fixture
def pair() -> list[Master]:
    return [Master({"wght": 400}, _font(86, "Regular")), Master({"wght": 700}, _font(130, "Bold"))]


def test_compatible_pair(pair: list[Master]) -> None:
    assert check_masters(pair) == []
    assert axis_ranges(pair) == {"wght": (400, 400, 700)}


def test_default_is_first_master() -> None:
    masters = [
        Master({"wght": 400}, _font(86, "Regular")),
        Master({"wght": 200}, _font(50, "Light")),
        Master({"wght": 800}, _font(140, "Black")),
    ]
    assert axis_ranges(masters) == {"wght": (200, 400, 800)}
    assert masters[0].style_name == "Regular"
    assert Master({"wght": 1}, masters[0].font, name="Book").style_name == "Book"


def test_needs_two_masters(pair: list[Master]) -> None:
    assert check_masters(pair[:1]) == ["need at least two masters"]


def test_location_problems(pair: list[Master]) -> None:
    same = [pair[0], Master({"wght": 400}, pair[1].font)]
    assert any("share location" in p for p in check_masters(same))
    axes = [pair[0], Master({"wdth": 100}, pair[1].font)]
    assert any("axes" in p for p in check_masters(axes))


def test_family_and_glyph_set(pair: list[Master]) -> None:
    other = Master({"wght": 700}, _font(130, "Bold", family="Other"))
    assert any("family" in p for p in check_masters([pair[0], other]))
    pair[1].font.remove_glyph("b")
    assert any("glyph set differs by ['b']" in p for p in check_masters(pair))


def test_incompatible_outline(pair: list[Master]) -> None:
    pair[1].font.add_glyph(
        Glyph("n", Outline(pair[1].font["o"].outline.contours[:1]), 500, unicodes=(ord("n"),)),
        replace=True,
    )
    assert any(p.startswith("glyph 'n':") for p in check_masters(pair))


def test_kerning_groups_must_match(pair: list[Master]) -> None:
    pair[0].font.add_class_kern_table(ClassKernTable(classes=(KernClass("round", ("o",)),)))
    assert any("kerning groups differ" in p for p in check_masters(pair))


def test_anchor_mismatch(pair: list[Master]) -> None:
    g = pair[1].font["o"]
    pair[1].font.add_glyph(
        Glyph(g.name, g.outline, g.advance, unicodes=g.unicodes, anchors=()), replace=True
    )
    assert any("anchors differ" in p for p in check_masters(pair))
