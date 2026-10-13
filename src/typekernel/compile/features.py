"""Minimal OpenType feature strings for compiled fonts."""

from __future__ import annotations

from typekernel.font import Font
from typekernel.parts.figures import tabular

__all__ = ["add_tabular_alternates", "standard_feature_text"]


def add_tabular_alternates(font: Font, digits: dict[str, object]) -> None:
    """Register ``zero.tf`` … ``nine.tf`` from :func:`~typekernel.parts.figures.tabular`."""
    from typekernel.font import Glyph
    from typekernel.parts.compose import ComposedGlyph

    tab = tabular({k: v for k, v in digits.items() if isinstance(v, ComposedGlyph)})
    for ch, g in tab.items():
        base = font.resolve(ch)
        if base is None:
            continue
        name = f"{base}.tf"
        font.add_glyph(Glyph.from_composed(name, g, unicodes=()), replace=True)


def standard_feature_text(*, tnum: bool = True, liga: bool = True) -> str:
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
    return "\n\n".join(lines) + "\n"
