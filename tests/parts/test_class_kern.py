"""Synthetic fixtures for class-based kerning."""

from __future__ import annotations

import pytest

from typekernel.optics.space import pair_gap_optical, with_sidebearings
from typekernel.parts import (
    ClassKernTable,
    DesignContext,
    GlyphAssembler,
    KernClass,
    auto_class_kern,
    bowl,
    default_latin_kern_classes,
    diagonal_stem,
    rhythm_from_control_glyphs,
    vertical_stem,
)


def _pack(asm: GlyphAssembler, lsb: float = 40.0, rsb: float = 40.0):
    return with_sidebearings(asm.build(), lsb, rsb)


@pytest.fixture()
def synth_glyphs() -> dict:
    ctx = DesignContext.geometric_sans()
    n = _pack(
        GlyphAssembler(ctx)
        .add(vertical_stem(ctx, 0.0, 0.0, ctx.x_height))
        .add(vertical_stem(ctx, 180.0, 0.0, ctx.x_height * 0.55))
    )
    outer, hole = bowl(
        ctx, 90.0, ctx.x_height / 2.0, rx=80.0, ry=ctx.x_height / 2.0 + ctx.overshoot
    )
    o = _pack(GlyphAssembler(ctx).add(outer).add_hole(hole))
    v = _pack(
        GlyphAssembler(ctx)
        .add(diagonal_stem(ctx, 0.0, ctx.x_height, 70.0, 0.0, compensate=True))
        .add(diagonal_stem(ctx, 70.0, 0.0, 140.0, ctx.x_height, compensate=True))
    )
    return {"n": n, "h": n, "o": o, "c": o, "v": v, "y": v}


@pytest.fixture()
def synth_classes() -> tuple[KernClass, ...]:
    return (
        KernClass("straight", ("n", "h")),
        KernClass("round", ("o", "c")),
        KernClass("diagonal", ("v", "y")),
    )


def test_kern_class_rejects_empty() -> None:
    with pytest.raises(ValueError):
        KernClass("x", ())


def test_rhythm_from_controls(synth_glyphs: dict) -> None:
    spec = rhythm_from_control_glyphs(synth_glyphs["n"], synth_glyphs["o"])
    assert spec.target_gap > 0
    assert spec.source == "control_glyphs"


def test_auto_class_kern_pulls_diagonal_round(
    synth_glyphs: dict, synth_classes: tuple[KernClass, ...]
) -> None:
    rhythm = rhythm_from_control_glyphs(synth_glyphs["n"])
    table = auto_class_kern(synth_glyphs, synth_classes, target=rhythm)
    # Diagonal against round has extra silhouette white → negative class kern
    diag_round = table.lookup_classes("diagonal", "round")
    straight_straight = table.lookup_classes("straight", "straight")
    assert diag_round < straight_straight - 5.0
    assert diag_round < -5.0
    # Glyph-level lookup via membership
    assert table.lookup("v", "o") == pytest.approx(diag_round)
    assert table.lookup("y", "c") == pytest.approx(diag_round)


def test_expand_flattens_class_pairs(
    synth_glyphs: dict, synth_classes: tuple[KernClass, ...]
) -> None:
    table = auto_class_kern(
        synth_glyphs, synth_classes, target=rhythm_from_control_glyphs(synth_glyphs["n"])
    )
    flat = table.expand()
    assert flat.lookup("v", "o") == pytest.approx(table.lookup("v", "o"))
    assert flat.lookup("y", "c") == pytest.approx(table.lookup("v", "o"))
    assert flat.lookup("n", "n") == pytest.approx(table.lookup("n", "n"))


def test_class_kern_closes_optical_gap(
    synth_glyphs: dict, synth_classes: tuple[KernClass, ...]
) -> None:
    rhythm = rhythm_from_control_glyphs(synth_glyphs["n"])
    table = auto_class_kern(synth_glyphs, synth_classes, target=rhythm)
    k = table.lookup("v", "o")
    before = pair_gap_optical(synth_glyphs["v"], synth_glyphs["o"], kern=0.0)
    after = pair_gap_optical(synth_glyphs["v"], synth_glyphs["o"], kern=k)
    assert abs(after - rhythm.target_gap) < abs(before - rhythm.target_gap)
    assert abs(after - rhythm.target_gap) < 2.0


def test_to_fea_contains_classes_and_pos(
    synth_glyphs: dict, synth_classes: tuple[KernClass, ...]
) -> None:
    table = auto_class_kern(synth_glyphs, synth_classes, target=40.0)
    fea = table.to_fea()
    assert "@straight_left = [n h];" in fea
    assert "pos @diagonal_left @round_right" in fea
    assert fea.strip().startswith("feature kern {")
    assert fea.strip().endswith("} kern;")


def test_with_pair_and_default_classes() -> None:
    classes = default_latin_kern_classes()
    assert any(c.name == "round" for c in classes)
    table = ClassKernTable(classes, ())
    table2 = table.with_pair("diagonal", "round", -20.0)
    assert table2.lookup_classes("diagonal", "round") == -20.0
    assert table.lookup_classes("diagonal", "round") == 0.0


def test_split_side_classes_export_different_kern1_kern2() -> None:
    from typekernel.font import Font
    from typekernel.optics.space import space_font
    from typekernel.parts import DesignContext, FormSources, auto_side_kern_classes

    ctx = DesignContext.code_clear()
    controls = FormSources.from_context(ctx)
    spaced = space_font(controls.derive(), ctx)
    classes = auto_side_kern_classes(spaced, ctx)
    font = Font.from_context(ctx, "Side Kern")
    font.add_chars({ch: spaced[ch] for ch in "bno"})
    font.add_class_kern_table(
        auto_class_kern(
            spaced, classes, target=rhythm_from_control_glyphs(spaced["n"], spaced["o"])
        )
    )
    left = font.groups.get("public.kern1.straight", ())
    right = font.groups.get("public.kern2.round", ())
    assert "b" in left or "n" in left
    assert "b" in right or "o" in right
    if "b" in left and "b" in right:
        assert "public.kern1.straight" in font.groups
        assert "public.kern2.round" in font.groups


def test_capitals_are_classed_without_ho_controls() -> None:
    """A proof set with I/B but not H/O must still kern those capitals."""
    from typekernel.optics.glyph_polish import GlyphPolishOptions, polish_glyph_map
    from typekernel.optics.space import pair_gap_optical, space_font
    from typekernel.parts import (
        DesignContext,
        FormSources,
        auto_class_kern,
        auto_side_kern_classes,
        rhythm_from_control_glyphs,
    )

    controls = FormSources.from_context(DesignContext.code_clear())
    drawn = polish_glyph_map(
        controls.derive("IdrBuno"),
        GlyphPolishOptions(joins_policy="tangent_fix"),
    )
    assert "H" not in drawn and "O" not in drawn
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, controls.context, rhythm=rhythm)
    classes = auto_side_kern_classes(spaced, controls.context)
    assert any("I" in kc.members for kc in classes)
    kern = auto_class_kern(spaced, classes, target=rhythm)
    gap = pair_gap_optical(spaced["I"], spaced["d"], kern=kern.lookup("I", "d"))
    assert abs(gap - rhythm.target_gap) < 2.0


def test_skip_same_class(synth_glyphs: dict, synth_classes: tuple[KernClass, ...]) -> None:
    table = auto_class_kern(
        synth_glyphs, synth_classes, target=50.0, skip_same_class=True
    )
    assert all(p.left_class != p.right_class for p in table.pairs)
