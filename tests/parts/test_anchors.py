"""Anchors and design records travel with a ComposedGlyph."""

from __future__ import annotations

import pytest

from typekernel.font import Anchor as FontAnchor
from typekernel.font import Glyph
from typekernel.geo.layout import union_bounds
from typekernel.optics.space import with_sidebearings
from typekernel.parts import Anchor, DesignContext, GlyphAssembler, vertical_stem


def _stem_glyph(ctx: DesignContext):
    return (
        GlyphAssembler(ctx)
        .add(vertical_stem(ctx, 100.0, 0.0, ctx.x_height))
        .anchor("top", 100.0 + ctx.stem / 2, ctx.x_height)
        .anchor("bottom", 100.0 + ctx.stem / 2, 0.0)
        .with_design({"kind": "stem"})
        .build()
    )


def _ink_center(g) -> float:
    box = union_bounds(list(g.solids))
    return (box[0] + box[2]) / 2


def test_font_anchor_is_parts_anchor() -> None:
    assert FontAnchor is Anchor


def test_assembler_shifts_anchors_with_ink() -> None:
    ctx = DesignContext.code_clear()
    g = _stem_glyph(ctx)
    assert g.anchor("top").x == pytest.approx(_ink_center(g))
    assert g.anchor("top").y == ctx.x_height
    assert g.design == {"kind": "stem"}
    with pytest.raises(KeyError):
        g.anchor("ogonek")


def test_anchor_name_replaced_not_duplicated() -> None:
    ctx = DesignContext.code_clear()
    g = (
        GlyphAssembler(ctx)
        .add(vertical_stem(ctx, 0.0, 0.0, 100.0))
        .anchor("top", 0, 0)
        .anchor("top", 5, 5)
        .build()
    )
    assert [a.name for a in g.anchors] == ["top"]


def test_with_sidebearings_moves_anchors_and_keeps_design() -> None:
    ctx = DesignContext.code_clear()
    g = with_sidebearings(_stem_glyph(ctx), 200.0, 10.0)
    assert g.anchor("top").x == pytest.approx(_ink_center(g))
    assert g.design == {"kind": "stem"}
    assert g.advance == pytest.approx(200.0 + ctx.stem + 10.0)


def test_glyph_from_composed_keeps_and_overrides_anchors() -> None:
    ctx = DesignContext.code_clear()
    g = _stem_glyph(ctx)
    glyph = Glyph.from_composed("i", g, anchors=(Anchor("top", 1.0, 2.0), Anchor("ogonek", 3, 0)))
    by_name = {a.name: (a.x, a.y) for a in glyph.anchors}
    assert by_name["top"] == (1.0, 2.0)
    assert by_name["bottom"][1] == 0.0
    assert "ogonek" in by_name
