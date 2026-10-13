"""Punctuation registered on the control sheet and builds cleanly."""

from __future__ import annotations

from typekernel.parts import PUNCT_FORMS, Controls, DesignContext


def test_punct_forms_build() -> None:
    ctx = DesignContext.code_clear()
    glyphs = Controls.from_context(ctx).build_all(".,;!?-")
    for ch in ".,;!?-":
        assert ch in glyphs
        assert glyphs[ch].advance > 0


def test_sentence_chars_in_supported() -> None:
    controls = Controls.from_context(DesignContext.code_clear())
    supported = controls.supported
    for ch in ".,;:!?\"'()[]/":
        assert ch in supported or ch in PUNCT_FORMS
