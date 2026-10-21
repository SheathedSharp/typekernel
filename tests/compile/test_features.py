"""OpenType feature helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("ufoLib2")
pytest.importorskip("ufo2ft")

from typekernel.compile import FamilyBuildOptions, build_font, compose_font
from typekernel.compile.features import (
    add_fraction_forms,
    add_ordn_forms,
    add_standard_ligatures,
    standard_feature_text,
)
from typekernel.font import Font
from typekernel.parts import DesignContext, FormSources


def test_liga_glyphs_and_fea(tmp_path) -> None:
    ctx = DesignContext.code_clear()
    controls = FormSources.from_context(ctx)
    font = Font.from_context(ctx, "Feat")
    font.add_chars(controls.derive("fli"))
    add_standard_ligatures(font, controls.control_glyphs())
    font.features = standard_feature_text(tnum=False, case=False)
    build_font(font, tmp_path, formats=("otf",))
    assert "fi" in font and "fl" in font
    assert "feature liga" in font.features


def test_frac_and_ordn_glyphs_and_fea(tmp_path) -> None:
    ctx = DesignContext.code_clear()
    controls = FormSources.from_context(ctx)
    font = Font.from_context(ctx, "FracOrdn")
    drawn = controls.derive("0123456789/aoNnMm")
    font.add_chars(drawn)
    add_fraction_forms(font, {ch: drawn[ch] for ch in "0123456789"}, slash=drawn["/"])
    add_ordn_forms(font, drawn)
    font.features = standard_feature_text(tnum=False, liga=False, case=False, frac=True, ordn=True)
    build_font(font, tmp_path, formats=("otf",))
    assert "one.numr" in font and "one.dnom" in font
    assert "fraction" in font
    assert "ordfeminine" in font and "ordmasculine" in font
    assert "feature frac" in font.features
    assert "feature ordn" in font.features
    assert "feature numr" in font.features


def test_compose_font_frac_ordn_options(tmp_path) -> None:
    controls = FormSources.from_context(DesignContext.humanist_sans())
    font = compose_font(
        controls.derive(),
        controls.context,
        "ComposeFrac",
        options=FamilyBuildOptions(frac=True, ordn=True),
    )
    build_font(font, tmp_path, formats=("otf",))
    assert "zero.numr" in font
    assert "ordfeminine" in font
    assert "feature frac" in font.features
