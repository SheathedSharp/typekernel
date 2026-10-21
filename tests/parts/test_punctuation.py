"""Punctuation registered on the control sheet and builds cleanly."""

from __future__ import annotations

import pytest

from typekernel.axes.interpolatable import check_interpolatable
from typekernel.font import Glyph
from typekernel.parts import PUNCT_FORMS, DesignContext, FormSources
from typekernel.qa.identity import _hole_contour_count
from typekernel.qa.thickness import _point_in_ink


def test_punct_forms_build() -> None:
    ctx = DesignContext.code_clear()
    glyphs = FormSources.from_context(ctx).derive(".,;!?-")
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
        Glyph.from_composed("&", FormSources.from_context(base.tuned(stem=s)).derive_one("&")).outline
        for s in stems
    ]
    assert check_interpolatable(outlines) == []


def test_dollar_waist_coupled_topology() -> None:
    ctx = DesignContext.code_clear()
    g = FormSources.from_context(ctx).derive_one("$")
    assert len(g.solids) == 1
    assert _hole_contour_count(g) == 2
    assert len(g.solids[0].contours) == 3
    cx = g.advance / 2.0
    assert _point_in_ink(cx, ctx.x_height * 0.5, g)
    assert _point_in_ink(cx - ctx.stem * 0.35, 0.5, g)
    assert _point_in_ink(cx, ctx.x_height - 0.5, g)
    assert len(g.solids[0].contours[0].segments) == 15


@pytest.mark.parametrize(
    "preset",
    ("humanist_sans", "code_clear", "geometric_sans"),
)
def test_dollar_interpolates_across_stems(preset: str) -> None:
    base = getattr(DesignContext, preset)()
    stems = (50.0, base.stem, 140.0)
    outlines = [
        Glyph.from_composed("$", FormSources.from_context(base.tuned(stem=s)).derive_one("$")).outline
        for s in stems
    ]
    assert check_interpolatable(outlines) == []


@pytest.mark.parametrize(
    "preset",
    ("humanist_sans", "code_clear", "geometric_sans"),
)
def test_hash_interpolates_across_stems(preset: str) -> None:
    base = getattr(DesignContext, preset)()
    stems = (50.0, base.stem, 140.0)
    outlines = [
        Glyph.from_composed("#", FormSources.from_context(base.tuned(stem=s)).derive_one("#")).outline
        for s in stems
    ]
    assert check_interpolatable(outlines) == []


def test_hash_outer_segment_count_fixed_across_stems() -> None:
    ctx = DesignContext.humanist_sans()
    ref = len(FormSources.from_context(ctx).derive_one("#").solids[0].contours[0].segments)
    for stem in (30.0, 86.0, 220.0):
        g = FormSources.from_context(ctx.tuned(stem=stem)).derive_one("#")
        assert len(g.solids[0].contours[0].segments) == ref


@pytest.mark.parametrize(
    "preset",
    ("humanist_sans", "code_clear", "geometric_sans"),
)
def test_percent_interpolates_across_stems(preset: str) -> None:
    base = getattr(DesignContext, preset)()
    stems = (50.0, base.stem, 140.0)
    outlines = [
        Glyph.from_composed("%", FormSources.from_context(base.tuned(stem=s)).derive_one("%")).outline
        for s in stems
    ]
    assert check_interpolatable(outlines) == []


def test_ampersand_tail_reaches_baseline() -> None:
    from typekernel.geo.layout import union_bounds

    glyph = FormSources.from_context(DesignContext.humanist_sans()).derive_one("&")
    assert len(glyph.solids) == 2
    assert len(glyph.holes) == 2
    y0 = union_bounds(list(glyph.solids))[1]
    assert y0 < glyph.context.x_height * 0.05


def test_at_sign_inner_bowl_has_counter() -> None:
    glyph = FormSources.from_context(DesignContext.humanist_sans()).derive_one("@")
    assert len(glyph.solids) == 2
    assert len(glyph.holes) == 2


@pytest.mark.parametrize(
    "preset",
    ("humanist_sans", "code_clear", "geometric_sans"),
)
def test_at_sign_interpolates_across_stems(preset: str) -> None:
    base = getattr(DesignContext, preset)()
    stems = (50.0, base.stem, 140.0)
    outlines = [
        Glyph.from_composed("@", FormSources.from_context(base.tuned(stem=s)).derive_one("@")).outline
        for s in stems
    ]
    assert check_interpolatable(outlines) == []


def test_sentence_chars_in_supported() -> None:
    controls = FormSources.from_context(DesignContext.code_clear())
    supported = controls.supported
    for ch in ".,;:!?\"'()[]/":
        assert ch in supported or ch in PUNCT_FORMS
