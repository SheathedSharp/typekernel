"""Glyph-level join polish."""

from __future__ import annotations

from typekernel.geo.smoothness import is_g1_join
from typekernel.optics.glyph_polish import GlyphPolishOptions, polish_glyph
from typekernel.parts import Controls, DesignContext


def _non_g1_count(g):
    return sum(
        1
        for o in g.solids
        for c in o.contours
        for i in range(len(c.segments))
        if not is_g1_join(c.segments[i], c.segments[(i + 1) % len(c.segments)])
    )


def test_polish_reduces_kinks_on_control_n() -> None:
    ctx = DesignContext.code_clear()
    raw = Controls.from_context(ctx).build("n")
    polished = polish_glyph(raw, GlyphPolishOptions(joins_policy="tangent_fix"))
    assert _non_g1_count(polished) <= _non_g1_count(raw)


def test_compose_polish_noop_identity() -> None:
    ctx = DesignContext.code_clear()
    g = Controls.from_context(ctx).build("o")
    same = polish_glyph(g, GlyphPolishOptions.noop())
    assert same is g
