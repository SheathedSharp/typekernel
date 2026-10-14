"""Punctuation registered on the control sheet and builds cleanly."""

from __future__ import annotations

from typekernel.parts import PUNCT_FORMS, Controls, DesignContext


def test_punct_forms_build() -> None:
    ctx = DesignContext.code_clear()
    glyphs = Controls.from_context(ctx).build_all(".,;!?-")
    for ch in ".,;!?-":
        assert ch in glyphs
        assert glyphs[ch].advance > 0


def test_ampersand_tail_reaches_baseline() -> None:
    from typekernel.geo.layout import union_bounds

    glyph = Controls.from_context(DesignContext.humanist_sans()).build("&")
    assert len(glyph.solids) == 2
    assert len(glyph.holes) == 2
    y0 = union_bounds(list(glyph.solids))[1]
    assert y0 < glyph.context.x_height * 0.05


def test_at_sign_inner_bowl_has_counter() -> None:
    glyph = Controls.from_context(DesignContext.humanist_sans()).build("@")
    assert len(glyph.solids) == 2
    assert len(glyph.holes) == 2


def test_sentence_chars_in_supported() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    supported = controls.supported
    for ch in ".,;:!?\"'()[]/":
        assert ch in supported or ch in PUNCT_FORMS
