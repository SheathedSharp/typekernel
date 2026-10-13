"""Register combining marks and precomposed Latin-1 accents on a :class:`Font`."""

from __future__ import annotations

from typekernel.font import Font, Glyph
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.control import build_n, build_o, dotless_i_from_n, dotless_j_from_n
from typekernel.parts.marks import MARK_BUILDERS, MARK_UNICODE

__all__ = ["COMPOSITE_LATIN", "add_composite_latin", "add_marks"]

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
    ("Á", "A", "acutecomb", "top", "_top"),
    ("É", "E", "acutecomb", "top", "_top"),
    ("Í", "I", "acutecomb", "top", "_top"),
    ("Ó", "O", "acutecomb", "top", "_top"),
    ("Ú", "U", "acutecomb", "top", "_top"),
    ("Ç", "C", "cedillacomb", "bottom", "_bottom"),
    ("Ñ", "N", "tildecomb", "top", "_top"),
    ("ñ", "n", "tildecomb", "top", "_top"),
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
