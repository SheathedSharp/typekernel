"""Punctuation registered on the control sheet and builds cleanly."""

from __future__ import annotations

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.font import Glyph
from typekernel.parts import PUNCT_FORMS, Controls, DesignContext


def test_punct_forms_build() -> None:
    ctx = DesignContext.code_clear()
    glyphs = Controls.from_context(ctx).build_all(".,;!?-")
    for ch in ".,;!?-":
        assert ch in glyphs
        assert glyphs[ch].advance > 0


@pytest.mark.parametrize(
    "preset",
    ("humanist_sans", "code_clear", "geometric_sans"),
)
def test_ampersand_interpolates_across_stems(preset: str) -> None:
    base = getattr(DesignContext, preset)()
    stems = (50.0, base.stem, 140.0)
    outlines = [
        Glyph.from_composed("&", Controls.from_context(base.tuned(stem=s)).build("&")).outline
        for s in stems
    ]
    assert check_interpolatable(outlines) == []


@pytest.mark.parametrize(
    "preset",
    ("humanist_sans", "code_clear", "geometric_sans"),
)
def test_dollar_interpolates_across_stems(preset: str) -> None:
    base = getattr(DesignContext, preset)()
    stems = (50.0, base.stem, 140.0)
    outlines = [
        Glyph.from_composed("$", Controls.from_context(base.tuned(stem=s)).build("$")).outline
        for s in stems
    ]
    assert check_interpolatable(outlines) == []


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
