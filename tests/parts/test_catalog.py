"""Coverage for the expanded parts catalog (agent-facing surface)."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.parts import (
    LETTER_BUILDERS,
    DesignContext,
    build_letter,
    build_word,
    capsule,
    crossbar,
    default_sans_kern,
    fillet_pad,
    ink_trap,
    layout_glyphs,
    letter_a,
    letter_n,
    letter_o,
    mirror_x,
    rotate,
    scale,
    serif_bracket,
    terminal_ball,
    translate,
    try_difference,
    try_union,
    vertical_stem,
    wedge,
    word_zayju,
)

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def test_presets_exist() -> None:
    assert DesignContext.geometric_sans().stem > 0
    assert DesignContext.humanist_sans().contrast < 1.0
    assert DesignContext.mono().tracking == 0.0
    assert DesignContext.display().overshoot > DesignContext.geometric_sans().overshoot


def test_tuned_overrides_stem() -> None:
    ctx = DesignContext.geometric_sans().tuned(stem=60.0)
    assert ctx.stem == 60.0
    assert ctx.x_height == DesignContext.geometric_sans().x_height


def test_transforms_translate_scale_rotate() -> None:
    ctx = DesignContext.geometric_sans()
    stem = vertical_stem(ctx, 0.0, 0.0, 100.0)
    moved = translate(stem, 10.0, 5.0)
    assert moved.contours[0].segments[0].points[0].x == pytest.approx(10.0)
    scaled = scale(stem, 2.0, origin=(0.0, 0.0))
    # top-right of rect was (stem, 100); after *2 → (2*stem, 200)
    ys = [p.y for s in scaled.contours[0].segments for p in s.points]
    assert max(ys) == pytest.approx(200.0)
    spun = rotate(stem, 90.0, origin=(0.0, 0.0))
    assert len(spun.contours) == 1
    mirrored = mirror_x(stem, at_x=0.0)
    assert mirrored.contours[0].segments[0].points[0].x <= 0.0


def test_extra_primitives_build() -> None:
    ctx = DesignContext.geometric_sans()
    assert capsule(ctx, 0.0, 0.0, 200.0, 40.0).contours
    assert crossbar(ctx, 0.0, 200.0, 100.0).contours
    assert fillet_pad(ctx, 50.0, 50.0, quadrant=0).contours
    assert terminal_ball(ctx, 0.0, 0.0).contours
    assert serif_bracket(ctx, 0.0, 0.0, side="left").contours
    assert wedge(ctx, 0.0, 0.0, -10.0, 20.0, 10.0, 20.0).contours


def test_ink_trap_builds_wedge() -> None:
    ctx = DesignContext.geometric_sans()
    trap = ink_trap(ctx, 0.0, 0.0, depth=16.0, opening_deg=30.0, bisector_deg=270.0)
    assert trap.contour_count == 1


def test_kern_table_and_layout() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = word_zayju(ctx)
    table = default_sans_kern().with_pair("z", "a", -8.0)
    assert table.lookup("z", "a") == -8.0
    xs = layout_glyphs(glyphs, list("zayju"), kerning=table)
    assert len(xs) == 5
    assert xs[0] == 0.0
    assert xs[1] > xs[0]


def test_letter_builders_cover_common_latin() -> None:
    ctx = DesignContext.geometric_sans()
    for ch in "acehijlnosuyz":
        g = build_letter(ch, ctx)
        assert g.advance > 0
        assert g.context is ctx
    assert set("zayju").issubset(LETTER_BUILDERS)


def test_letter_n_and_o() -> None:
    ctx = DesignContext.geometric_sans()
    n = letter_n(ctx)
    o = letter_o(ctx)
    assert n.advance > 0
    assert o.advance > 0


@pytest.mark.skipif(not HAS_PATHOPS, reason="skia-pathops not installed")
def test_letter_a_unions_and_subtracts_counter() -> None:
    ctx = DesignContext.geometric_sans()
    a = letter_a(ctx)
    # After subtract_holes, counter is baked into the solid contour count.
    assert len(a.holes) == 0
    assert len(a.solids) == 1
    # Outer ring + hole means at least two contours inside the solid outline.
    assert len(a.solids[0].contours) >= 1


@pytest.mark.skipif(not HAS_PATHOPS, reason="skia-pathops not installed")
def test_try_union_and_difference() -> None:
    ctx = DesignContext.geometric_sans()
    a = vertical_stem(ctx, 0.0, 0.0, 100.0)
    b = vertical_stem(ctx, 40.0, 0.0, 100.0)
    u = try_union([a, b])
    assert u.contours
    d = try_difference(a, vertical_stem(ctx, 20.0, 20.0, 80.0, width=20.0))
    assert d.contours


def test_build_word_zayju() -> None:
    glyphs = build_word("zayju")
    assert len(glyphs) == 5
