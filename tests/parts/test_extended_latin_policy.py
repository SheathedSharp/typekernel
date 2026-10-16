"""Extended Latin opt-in policy and composite lint."""

from __future__ import annotations

import pytest

from typekernel.compile import FamilyBuildOptions, compose_font_from_controls
from typekernel.parts import Controls, DesignContext
from typekernel.parts.diacritics import (
    COMPOSITE_LATIN,
    EXTENDED_LATIN_OUTLINE_CHARS,
    composite_latin_charset,
)
from typekernel.qa.composite import composed_glyph_from_font
from typekernel.qa.lint import lint_controls, lint_glyph

_BUILTIN_PRESETS = (
    "code_clear",
    "humanist_sans",
    "geometric_sans",
    "mono",
    "display",
    "open_print",
    "paper_ink",
    "slab_serif",
    "bracketed_serif",
)

_ACCENT_SAMPLES = "çéñ"


def test_extended_latin_not_in_default_supported() -> None:
    controls = Controls.from_context(DesignContext.humanist_sans())
    supported = controls.supported
    for ch in _ACCENT_SAMPLES + EXTENDED_LATIN_OUTLINE_CHARS:
        assert ch not in supported
    for ch in composite_latin_charset():
        assert ch not in supported


def test_composite_charset_matches_composite_latin_table() -> None:
    expected = {row[0] for row in COMPOSITE_LATIN}
    assert set(composite_latin_charset()) == expected


@pytest.mark.parametrize("preset", _BUILTIN_PRESETS)
def test_outline_extended_latin_lint_clean(preset: str) -> None:
    controls = Controls.from_context(getattr(DesignContext, preset)())
    report = lint_controls(controls, EXTENDED_LATIN_OUTLINE_CHARS)
    assert not report.errors


@pytest.mark.parametrize("preset", _BUILTIN_PRESETS)
def test_opt_in_composites_bake_to_lint_clean_glyphs(preset: str) -> None:
    controls = Controls.from_context(getattr(DesignContext, preset)())
    font = compose_font_from_controls(
        controls,
        "Extended Latin",
        options=FamilyBuildOptions(liga=True, extended_latin=EXTENDED_LATIN_OUTLINE_CHARS),
    )
    assert font.validate() == []
    ctx = controls.context
    for char in composite_latin_charset():
        name = font.cmap()[ord(char)]
        baked = composed_glyph_from_font(font, name)
        issues = [i for i in lint_glyph(baked, ctx, glyph_name=char) if i.severity == "error"]
        assert not issues, f"{preset} {char}: {issues}"
