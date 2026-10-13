"""FontInfo derives vertical metrics and zones from the design brief."""

from __future__ import annotations

import pytest

from typekernel.font import FontInfo, alignment_zones
from typekernel.parts import DesignContext


def test_from_context_copies_proportions() -> None:
    ctx = DesignContext.code_clear()
    info = FontInfo.from_context(ctx, "My Sans", "Bold", weight_class=700)
    assert info.family_name == "My Sans"
    assert info.style_name == "Bold"
    assert info.weight_class == 700
    assert info.units_per_em == ctx.units_per_em
    assert (info.ascender, info.descender) == (ctx.ascender, ctx.descender)
    assert (info.x_height, info.cap_height) == (ctx.x_height, ctx.cap_height)
    assert info.stem_snap_v == (ctx.stem,)
    assert info.stem_snap_h == (ctx.thin,)


@pytest.mark.parametrize("line_height", [1.2, 1.5])
def test_line_gap_hits_requested_line_height(line_height: float) -> None:
    ctx = DesignContext.code_clear()
    info = FontInfo.from_context(ctx, "X", line_height=line_height)
    total = info.ascender - info.descender + info.line_gap
    assert total == pytest.approx(line_height * ctx.units_per_em)


def test_line_gap_never_negative() -> None:
    ctx = DesignContext.code_clear()
    assert FontInfo.from_context(ctx, "X", line_height=0.5).line_gap == 0.0


def test_alignment_zones_follow_overshoot() -> None:
    ctx = DesignContext.code_clear()
    blues, others = alignment_zones(ctx)
    o = ctx.overshoot
    assert (-o, 0.0) in blues
    assert (ctx.x_height, ctx.x_height + o) in blues
    assert (ctx.cap_height, ctx.cap_height + o) in blues
    assert others == ((ctx.descender - o, ctx.descender),)


def test_alignment_zones_merge_when_cap_equals_ascender() -> None:
    ctx = DesignContext.code_clear().tuned(cap_height=760.0, ascender=765.0, overshoot=10.0)
    blues, _ = alignment_zones(ctx)
    assert (760.0, 775.0) in blues
    assert len(blues) == 3


def test_overrides_and_extra() -> None:
    ctx = DesignContext.code_clear()
    info = FontInfo.from_context(
        ctx, "X", line_gap=0.0, extra={"openTypeNameDesigner": "zayju", "xHeight": 999}
    )
    attrs = info.to_ufo_attributes()
    assert attrs["openTypeOS2TypoLineGap"] == 0
    assert attrs["openTypeNameDesigner"] == "zayju"
    assert attrs["xHeight"] == 999


def test_ufo_attributes_are_integers_and_use_typo_metrics() -> None:
    ctx = DesignContext.code_clear().tuned(ascender=770.4, descender=-219.6)
    attrs = FontInfo.from_context(ctx, "X").to_ufo_attributes()
    assert attrs["ascender"] == 770
    assert attrs["descender"] == -220
    assert attrs["openTypeOS2TypoAscender"] == attrs["openTypeHheaAscender"] == 770
    assert 7 in attrs["openTypeOS2Selection"]
    assert all(isinstance(v, int) for v in attrs["postscriptBlueValues"])
    assert len(attrs["postscriptBlueValues"]) % 2 == 0


def test_validation() -> None:
    with pytest.raises(ValueError):
        FontInfo(family_name="")
    with pytest.raises(ValueError):
        FontInfo(family_name="X", descender=10)
    with pytest.raises(ValueError):
        FontInfo(family_name="X", weight_class=0)
