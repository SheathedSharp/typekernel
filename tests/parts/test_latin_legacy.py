"""Deprecated ``parts.latin`` API (not re-exported from ``typekernel.parts``)."""

from __future__ import annotations

import importlib.util

from typekernel.parts import DesignContext, layout_glyphs
from typekernel.parts.latin import (
    LETTER_BUILDERS,
    build_letter,
    build_word,
    letter_a,
    letter_n,
    letter_o,
    word_zayju,
)

HAS_PATHOPS = importlib.util.find_spec("pathops") is not None


def test_legacy_letter_builders_cover_zayju() -> None:
    ctx = DesignContext.geometric_sans()
    for ch in "zayju":
        g = build_letter(ch, ctx)
        assert g.advance > 0
    assert set("zayju").issubset(LETTER_BUILDERS)


def test_legacy_word_zayju() -> None:
    ctx = DesignContext.geometric_sans()
    glyphs = word_zayju(ctx)
    assert len(glyphs) == 5
    xs = layout_glyphs(glyphs, list("zayju"))
    assert len(xs) == 5


def test_legacy_build_word() -> None:
    glyphs = build_word("zayju")
    assert len(glyphs) == 5


def test_legacy_letter_n_o_a() -> None:
    ctx = DesignContext.code_clear()
    assert letter_n(ctx).advance > 0
    assert letter_o(ctx).advance > 0
    assert letter_a(ctx).advance > 0
