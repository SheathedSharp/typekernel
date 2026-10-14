"""OpenType feature helpers (fea text + extra glyphs)."""

from __future__ import annotations

from collections.abc import Mapping

from typekernel.font import Font, Glyph, glyph_name_for_char
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.figures import tabular
from typekernel.parts.ligatures import fi_from_n, fl_from_n

__all__ = [
    "add_case_punctuation",
    "add_standard_ligatures",
    "add_tabular_alternates",
    "standard_feature_text",
]

_CASE_CHARS = ".,:;!?-"


def add_tabular_alternates(font: Font, digits: Mapping[str, ComposedGlyph]) -> None:
    """Register ``zero.tf`` … ``nine.tf`` from :func:`~typekernel.parts.figures.tabular`."""
    tab = tabular(dict(digits))
    for ch, g in tab.items():
        base = font.resolve(ch)
        if base is None:
            continue
        name = f"{base}.tf"
        font.add_glyph(Glyph.from_composed(name, g, unicodes=()), replace=True)


def add_standard_ligatures(font: Font, n_o: tuple[ComposedGlyph, ComposedGlyph]) -> None:
    """Add ``fi`` / ``fl`` ligature glyphs for GSUB ``liga``."""
    ctx = font.context
    if ctx is None:
        raise ValueError("font.context required")
    n, o = n_o
    for name, builder in (("fi", fi_from_n), ("fl", fl_from_n)):
        font.add_glyph(Glyph.from_composed(name, builder(n, o, ctx), unicodes=()), replace=True)


def add_case_punctuation(font: Font, glyphs: dict[str, ComposedGlyph]) -> None:
    """Duplicate key punctuation at cap-height for ``case`` feature."""
    ctx = font.context
    if ctx is None:
        raise ValueError("font.context required")
    shift = ctx.cap_height - ctx.x_height
    for ch in _CASE_CHARS:
        if ch not in glyphs:
            continue
        base = font.resolve(ch)
        if base is None:
            continue
        moved = glyphs[ch].translated(0.0, shift)
        font.add_glyph(Glyph.from_composed(f"{base}.case", moved, unicodes=()), replace=True)


def _case_glyph_names() -> tuple[str, ...]:
    return tuple(glyph_name_for_char(ch) for ch in _CASE_CHARS)


def standard_feature_text(*, tnum: bool = True, liga: bool = True, case: bool = True) -> str:
    """Return feaLib-ready feature code (``languagesystem`` + features)."""
    lines = ["languagesystem latn dflt;", "languagesystem latn TRK;"]
    if tnum:
        lines.append(
            "feature tnum {\n"
            "  sub zero by zero.tf;\n"
            "  sub one by one.tf;\n"
            "  sub two by two.tf;\n"
            "  sub three by three.tf;\n"
            "  sub four by four.tf;\n"
            "  sub five by five.tf;\n"
            "  sub six by six.tf;\n"
            "  sub seven by seven.tf;\n"
            "  sub eight by eight.tf;\n"
            "  sub nine by nine.tf;\n"
            "} tnum;"
        )
    if liga:
        lines.append(
            "feature liga {\n"
            "  sub f i by fi;\n"
            "  sub f l by fl;\n"
            "} liga;"
        )
    if case:
        subs = "\n  ".join(f"sub {base} by {base}.case;" for base in _case_glyph_names())
        lines.append(f"feature case {{\n  {subs}\n}} case;")
    return "\n\n".join(lines) + "\n"
