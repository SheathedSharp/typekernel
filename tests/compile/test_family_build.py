"""Feature-safe family assembly."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("ufoLib2")

from typekernel.compile import FamilyBuildOptions, build_font, compose_font, reference_kern_classes
from typekernel.parts import DesignContext, FormSources


def test_compose_liga_only_builds(tmp_path: Path) -> None:
    sheet = FormSources.from_context(DesignContext.code_clear())
    glyphs = sheet.derive()
    font = compose_font(
        glyphs,
        sheet.context,
        "Gate Test",
        options=FamilyBuildOptions(liga=True),
    )
    assert "fi" in font
    assert "sub f i by fi" in font.features
    assert "zero.tf" not in font.features
    build_font(font, tmp_path, formats=("otf",))


def test_compose_charset_subset() -> None:
    sheet = FormSources.from_context(DesignContext.geometric_sans())
    font = compose_font(
        sheet.derive("nhou"),
        sheet.context,
        "BodyOnly",
        options=FamilyBuildOptions(liga=False),
    )
    assert "n" in font
    assert "H" not in font


def test_reference_kern_classes_from_glyphs() -> None:
    sheet = FormSources.from_context(DesignContext.geometric_sans())
    glyphs = sheet.derive()
    assert reference_kern_classes(glyphs, sheet.context)


def test_compose_requires_n_and_o() -> None:
    sheet = FormSources.from_context(DesignContext.code_clear())
    glyphs = sheet.derive("h")
    with pytest.raises(KeyError, match="n"):
        compose_font(glyphs, sheet.context, "MissingNO")
