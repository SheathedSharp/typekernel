"""Register combining marks and precomposed Latin-1 accents on a :class:`Font`."""

from __future__ import annotations

from typekernel.font import Font, Glyph
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.control import build_n, build_o, dotless_i_from_n, dotless_j_from_n
from typekernel.parts.marks import CASE_MARK_BUILDERS, MARK_BUILDERS, MARK_UNICODE

__all__ = [
    "COMPOSITE_LATIN",
    "EXTENDED_LATIN_OUTLINE_CHARS",
    "add_composite_latin",
    "add_marks",
    "composite_latin_charset",
]

# TK-208: outline letters are opt-in via ``FamilyBuildOptions.extended_latin``;
# precomposed accents are registered when that option is non-empty (see
# ``compose_font``), not in ``FormSources.supported``.
EXTENDED_LATIN_OUTLINE_CHARS = "æøÆØ"


def composite_latin_charset() -> str:
    """All precomposed characters in :data:`COMPOSITE_LATIN` (stable order)."""
    return "".join(dict.fromkeys(char for char, *_ in COMPOSITE_LATIN))

# (character, base glyph name or char, mark glyph name, base anchor, mark anchor)
COMPOSITE_LATIN: tuple[tuple[str, str, str, str, str], ...] = (
    ("á", "a", "acutecomb", "top", "_top"),
    ("à", "a", "gravecomb", "top", "_top"),
    ("â", "a", "circumflexcomb", "top", "_top"),
    ("ä", "a", "dieresiscomb", "top", "_top"),
    ("ã", "a", "tildecomb", "top", "_top"),
    ("å", "a", "ringcomb", "top", "_top"),
    ("ç", "c", "cedillacomb", "bottom", "_bottom"),
    ("é", "e", "acutecomb", "top", "_top"),
    ("è", "e", "gravecomb", "top", "_top"),
    ("ê", "e", "circumflexcomb", "top", "_top"),
    ("ë", "e", "dieresiscomb", "top", "_top"),
    ("í", "dotlessi", "acutecomb", "top", "_top"),
    ("ì", "dotlessi", "gravecomb", "top", "_top"),
    ("î", "dotlessi", "circumflexcomb", "top", "_top"),
    ("ï", "dotlessi", "dieresiscomb", "top", "_top"),
    ("ó", "o", "acutecomb", "top", "_top"),
    ("ò", "o", "gravecomb", "top", "_top"),
    ("ô", "o", "circumflexcomb", "top", "_top"),
    ("ö", "o", "dieresiscomb", "top", "_top"),
    ("ú", "u", "acutecomb", "top", "_top"),
    ("ù", "u", "gravecomb", "top", "_top"),
    ("û", "u", "circumflexcomb", "top", "_top"),
    ("ü", "u", "dieresiscomb", "top", "_top"),
    ("ý", "y", "acutecomb", "top", "_top"),
    ("ÿ", "y", "dieresiscomb", "top", "_top"),
    ("Á", "A", "acutecomb.case", "top", "_top"),
    ("É", "E", "acutecomb.case", "top", "_top"),
    ("Í", "I", "acutecomb.case", "top", "_top"),
    ("Ó", "O", "acutecomb.case", "top", "_top"),
    ("Ú", "U", "acutecomb.case", "top", "_top"),
    ("Ç", "C", "cedillacomb", "bottom", "_bottom"),
    ("Ñ", "N", "tildecomb", "top", "_top"),
    ("ñ", "n", "tildecomb", "top", "_top"),
    ("õ", "o", "tildecomb", "top", "_top"),
    ("À", "A", "gravecomb.case", "top", "_top"),
    ("Â", "A", "circumflexcomb.case", "top", "_top"),
    ("Ä", "A", "dieresiscomb.case", "top", "_top"),
    ("Ã", "A", "tildecomb.case", "top", "_top"),
    ("Å", "A", "ringcomb.case", "top", "_top"),
    ("È", "E", "gravecomb.case", "top", "_top"),
    ("Ê", "E", "circumflexcomb.case", "top", "_top"),
    ("Ë", "E", "dieresiscomb.case", "top", "_top"),
    ("Ì", "I", "gravecomb.case", "top", "_top"),
    ("Î", "I", "circumflexcomb.case", "top", "_top"),
    ("Ï", "I", "dieresiscomb.case", "top", "_top"),
    ("Ò", "O", "gravecomb.case", "top", "_top"),
    ("Ô", "O", "circumflexcomb.case", "top", "_top"),
    ("Ö", "O", "dieresiscomb.case", "top", "_top"),
    ("Ù", "U", "gravecomb.case", "top", "_top"),
    ("Û", "U", "circumflexcomb.case", "top", "_top"),
    ("Ü", "U", "dieresiscomb.case", "top", "_top"),
    ("Ý", "Y", "acutecomb.case", "top", "_top"),
    ("Õ", "O", "tildecomb.case", "top", "_top"),
)


def add_marks(font: Font, n_o: tuple[ComposedGlyph, ComposedGlyph] | None = None) -> None:
    """Add default combining marks (``acutecomb``, …) with zero advance."""
    ctx = font.context
    if ctx is None:
        raise ValueError("font.context is required to draw marks")
    n, o = n_o or (build_n(ctx), build_o(ctx))
    for name, builder in MARK_BUILDERS.items():
        composed = builder(n, o, ctx)
        font.add_glyph(
            Glyph.from_composed(
                name,
                composed,
                unicodes=(MARK_UNICODE[name],),
            ),
            replace=True,
        )
    for name, builder in CASE_MARK_BUILDERS.items():
        composed = builder(n, o, ctx)
        font.add_glyph(Glyph.from_composed(name, composed), replace=True)


def _add_dotless_bases(font: Font, n_o: tuple[ComposedGlyph, ComposedGlyph]) -> None:
    n, _o = n_o
    ctx = font.context
    assert ctx is not None
    for char, builder in (("ı", dotless_i_from_n), ("ȷ", dotless_j_from_n)):
        composed = builder(n, ctx)
        font.add_glyph(Glyph.for_char(char, composed), replace=True)


def add_composite_latin(font: Font, n_o: tuple[ComposedGlyph, ComposedGlyph] | None = None) -> None:
    """Add marks, dotless ``i``/``j``, and :data:`COMPOSITE_LATIN` composites."""
    ctx = font.context
    if ctx is None:
        raise ValueError("font.context is required")
    n_o = n_o or (build_n(ctx), build_o(ctx))
    add_marks(font, n_o)
    _add_dotless_bases(font, n_o)
    for char, base, mark, ba, ma in COMPOSITE_LATIN:
        font.add_composite(char, base, ((mark, ba, ma),), replace=True)
