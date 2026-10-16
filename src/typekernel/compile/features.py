"""OpenType feature helpers (fea text + extra glyphs)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from typekernel.font import Font, Glyph, glyph_name_for_char
from typekernel.geo.layout import union_bounds
from typekernel.parts.compose import Anchor, ComposedGlyph
from typekernel.parts.figures import tabular
from typekernel.parts.ligatures import fi_from_n, fl_from_n
from typekernel.parts.transforms import scale, translate

__all__ = [
    "add_case_punctuation",
    "add_fraction_forms",
    "add_ordn_forms",
    "add_standard_ligatures",
    "add_tabular_alternates",
    "standard_feature_text",
]

_CASE_CHARS = ".,:;!?-"
_DIGIT_CHARS = "0123456789"
_DIGIT_NAMES = tuple(glyph_name_for_char(ch) for ch in _DIGIT_CHARS)

_FRAC_SCALE = 0.60
_ORDN_SCALE = 0.55


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


def _affine_glyph(
    glyph: ComposedGlyph,
    *,
    sx: float,
    sy: float,
    origin: tuple[float, float] = (0.0, 0.0),
    dx: float = 0.0,
    dy: float = 0.0,
    advance: float | None = None,
) -> ComposedGlyph:
    """Scale about ``origin``, then translate; advance defaults to ``sx`` times."""

    def xf(outline):
        return translate(scale(outline, sx, sy, origin=origin), dx, dy)

    ox, oy = origin
    anchors = tuple(
        Anchor(
            a.name,
            ox + (a.x - ox) * sx + dx,
            oy + (a.y - oy) * sy + dy,
        )
        for a in glyph.anchors
    )
    adv = glyph.advance * sx if advance is None else advance
    return replace(
        glyph,
        solids=tuple(xf(o) for o in glyph.solids),
        holes=tuple(xf(h) for h in glyph.holes),
        anchors=anchors,
        advance=adv,
    )


def _ink_bounds(glyph: ComposedGlyph) -> tuple[float, float, float, float]:
    return union_bounds(list(glyph.solids) + list(glyph.holes))


def add_fraction_forms(
    font: Font,
    digits: Mapping[str, ComposedGlyph],
    *,
    slash: ComposedGlyph | None = None,
) -> None:
    """Add ``.numr`` / ``.dnom`` digits and a ``fraction`` slash for ``frac``.

    Numerators sit on a raised baseline (~0.4×x-height); denominators stay near
    the baseline. ``fraction`` (U+2044) copies ``slash`` when provided, else
    the font's existing ``slash`` glyph.
    """
    ctx = font.context
    if ctx is None:
        raise ValueError("font.context required")
    xh = ctx.x_height
    for ch in _DIGIT_CHARS:
        if ch not in digits:
            continue
        base = font.resolve(ch)
        if base is None:
            continue
        g = digits[ch]
        scaled = _affine_glyph(g, sx=_FRAC_SCALE, sy=_FRAC_SCALE, origin=(0.0, 0.0))
        box = _ink_bounds(scaled)
        numr = scaled.translated(0.0, 0.40 * xh - box[1])
        dnom = scaled.translated(0.0, -box[1])
        font.add_glyph(Glyph.from_composed(f"{base}.numr", numr, unicodes=()), replace=True)
        font.add_glyph(Glyph.from_composed(f"{base}.dnom", dnom, unicodes=()), replace=True)

    if slash is not None:
        font.add_glyph(Glyph.from_composed("fraction", slash, unicodes=(0x2044,)), replace=True)
    elif "slash" in font:
        src = font["slash"]
        font.add_glyph(
            Glyph(
                name="fraction",
                outline=src.outline,
                advance=src.advance,
                unicodes=(0x2044,),
                anchors=src.anchors,
            ),
            replace=True,
        )


def add_ordn_forms(
    font: Font,
    glyphs: Mapping[str, ComposedGlyph],
) -> None:
    """Add ``ordfeminine`` / ``ordmasculine`` superiors for the ``ordn`` feature."""
    ctx = font.context
    if ctx is None:
        raise ValueError("font.context required")
    xh = ctx.x_height
    specs = (
        ("a", "ordfeminine", 0x00AA),
        ("o", "ordmasculine", 0x00BA),
    )
    for src_ch, name, cp in specs:
        if src_ch not in glyphs:
            continue
        g = glyphs[src_ch]
        scaled = _affine_glyph(g, sx=_ORDN_SCALE, sy=_ORDN_SCALE, origin=(0.0, 0.0))
        box = _ink_bounds(scaled)
        raised = scaled.translated(0.0, 0.55 * xh - box[1])
        font.add_glyph(Glyph.from_composed(name, raised, unicodes=(cp,)), replace=True)


def _case_glyph_names() -> tuple[str, ...]:
    return tuple(glyph_name_for_char(ch) for ch in _CASE_CHARS)


def _digit_sub_block(suffix: str) -> str:
    return "\n".join(f"  sub {name} by {name}.{suffix};" for name in _DIGIT_NAMES)


def standard_feature_text(
    *,
    tnum: bool = True,
    liga: bool = True,
    case: bool = True,
    frac: bool = False,
    ordn: bool = False,
) -> str:
    """Return feaLib-ready feature code (``languagesystem`` + features)."""
    nl = chr(10)
    lines = ["languagesystem latn dflt;", "languagesystem latn TRK;"]
    if tnum:
        lines.append(
            nl.join(
                [
                    "feature tnum {",
                    "  sub zero by zero.tf;",
                    "  sub one by one.tf;",
                    "  sub two by two.tf;",
                    "  sub three by three.tf;",
                    "  sub four by four.tf;",
                    "  sub five by five.tf;",
                    "  sub six by six.tf;",
                    "  sub seven by seven.tf;",
                    "  sub eight by eight.tf;",
                    "  sub nine by nine.tf;",
                    "} tnum;",
                ]
            )
        )
    if liga:
        lines.append(
            nl.join(
                [
                    "feature liga {",
                    "  sub f i by fi;",
                    "  sub f l by fl;",
                    "} liga;",
                ]
            )
        )
    if case:
        subs = (nl + "  ").join(
            f"sub {base} by {base}.case;" for base in _case_glyph_names()
        )
        lines.append(f"feature case {{{nl}  {subs}{nl}}} case;")
    if frac:
        digit_class = "[zero one two three four five six seven eight nine]"
        numr_class = (
            "[zero.numr one.numr two.numr three.numr four.numr "
            "five.numr six.numr seven.numr eight.numr nine.numr]"
        )
        dnom_class = (
            "[zero.dnom one.dnom two.dnom three.dnom four.dnom "
            "five.dnom six.dnom seven.dnom eight.dnom nine.dnom]"
        )
        lines.append(
            nl.join(["feature numr {", _digit_sub_block("numr"), "} numr;"])
        )
        lines.append(
            nl.join(["feature dnom {", _digit_sub_block("dnom"), "} dnom;"])
        )
        lines.append(
            nl.join(
                [
                    "feature frac {",
                    "  sub slash by fraction;",
                    "  lookup FRAC_NUMR {",
                    f"    sub {digit_class}' [slash fraction] by {numr_class};",
                    "  } FRAC_NUMR;",
                    "  lookup FRAC_DNOM {",
                    f"    sub [slash fraction] {digit_class}' by {dnom_class};",
                    "  } FRAC_DNOM;",
                    "} frac;",
                ]
            )
        )
    if ordn:
        lines.append(
            nl.join(
                [
                    "feature ordn {",
                    "  sub [N n] o by ordfeminine;",
                    "  sub [M m] o by ordmasculine;",
                    "} ordn;",
                ]
            )
        )
    return (nl + nl).join(lines) + nl
