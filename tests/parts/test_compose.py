"""Tests for GlyphAssembler composition."""

from __future__ import annotations

import importlib.util

import pytest

from typekernel.parts import (
    DesignContext,
    GlyphAssembler,
    horizontal_bar,
    letter_a,
    letter_z,
    vertical_stem,
    word_zayju,
)

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def test_assembler_without_union_keeps_separate_solids() -> None:
    ctx = DesignContext.geometric_sans()
    g = (
        GlyphAssembler(ctx)
        .add(vertical_stem(ctx, 0.0, 0.0, ctx.x_height))
        .add(horizontal_bar(ctx, 0.0, 200.0, 0.0))
        .build()
    )
    assert len(g.solids) == 2
    assert g.advance > 0
    assert g.context is ctx


@pytest.mark.skipif(not HAS_PATHOPS, reason="skia-pathops not installed")
def test_assembler_union_merges_solids() -> None:
    ctx = DesignContext.geometric_sans()
    g = (
        GlyphAssembler(ctx)
        .add(vertical_stem(ctx, 0.0, 0.0, ctx.x_height))
        .add(horizontal_bar(ctx, 0.0, 200.0, 0.0))
        .union_solids()
        .build()
    )
    assert len(g.solids) == 1


def test_word_zayju_shares_one_context() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = word_zayju(ctx)
    assert len(glyphs) == 5
    assert all(g.context is ctx for g in glyphs)
    assert all(g.advance > 0 for g in glyphs)


def test_letter_a_has_ink() -> None:
    ctx = DesignContext.geometric_sans()
    a = letter_a(ctx)
    assert a.advance > 0
    assert len(a.solids) >= 1
    if not HAS_PATHOPS:
        assert len(a.holes) == 1
        assert len(a.solids) >= 2


def test_letter_z_is_one_solid() -> None:
    ctx = DesignContext.geometric_sans()
    z = letter_z(ctx)
    assert len(z.solids) == 1
