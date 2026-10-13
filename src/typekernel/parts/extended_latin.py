"""Extra Latin-1 letters drawn as outlines (not mark composites)."""

from __future__ import annotations

from dataclasses import replace

from typekernel.geo.outline import Outline
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import _n_record, _o_record, _pack, a_from_o, e_from_o
from typekernel.parts.punctuation import _diagonal_slash

__all__ = [
    "EXTENDED_LATIN_FORMS",
    "AE_from_H_O",
    "Oslash_from_O",
    "ae_from_n_o",
    "oslash_from_o",
]


def _merge_solids(*parts: ComposedGlyph | Outline) -> tuple[Outline, ...]:
    solids: list[Outline] = []
    for p in parts:
        if isinstance(p, ComposedGlyph):
            solids.extend(p.solids)
        else:
            solids.append(p)
    return tuple(solids)


def oslash_from_o(
    o_glyph: ComposedGlyph,
    _n: ComposedGlyph,
    ctx: DesignContext | None = None,
) -> ComposedGlyph:
    """Lowercase ``ø``: ``o`` bowl plus a compensated slash."""
    c = ctx or o_glyph.context
    o = _o_record(o_glyph)
    slash = _diagonal_slash(c, _n_record(_n), back=False)
    return replace(o_glyph, solids=(*o_glyph.solids, slash), design=o)


def Oslash_from_O(
    _H: ComposedGlyph,
    O_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
) -> ComposedGlyph:
    """Uppercase ``Ø``: cap ``O`` plus slash (``n`` stem width from context)."""
    c = ctx or O_glyph.context
    from typekernel.parts.control import build_n, n_metrics

    slash = _diagonal_slash(c, _n_record(build_n(c, n_metrics(c))), back=False)
    return replace(O_glyph, solids=(*O_glyph.solids, slash))


def ae_from_n_o(
    n_glyph: ComposedGlyph,
    o_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
) -> ComposedGlyph:
    """Lowercase ``æ``: ``a`` + ``e`` with a shared advance."""
    c = ctx or n_glyph.context
    a = a_from_o(o_glyph, n_glyph, c)
    e = e_from_o(o_glyph, c)
    gap = c.stem * 0.08
    e_shift = e.translated(a.advance - gap)
    solids = _merge_solids(a, e_shift)
    adv = a.advance + e_shift.advance - gap
    g = _pack(c, a.design, {"top": (adv * 0.42, c.x_height)}, *solids)
    return replace(g, advance=adv)


def AE_from_H_O(
    H: ComposedGlyph,
    O: ComposedGlyph,
    ctx: DesignContext | None = None,
) -> ComposedGlyph:
    """Uppercase ``Æ``: cap ``E`` beside a narrowed ``A``-like left bowl."""
    c = ctx or H.context
    from typekernel.parts.caps import A_from_H, E_from_H

    a = A_from_H(H, c, width=0.82)
    e = E_from_H(H, c)
    gap = c.stem * 0.06
    e_shift = e.translated(a.advance - gap)
    solids = _merge_solids(a, e_shift)
    adv = a.advance + e_shift.advance - gap * 1.5
    g = _pack(c, H.design, {"top": (adv * 0.45, c.cap_height)}, *solids)
    return replace(g, advance=adv)


EXTENDED_LATIN_FORMS = {
    "æ": ae_from_n_o,
    "ø": oslash_from_o,
}

EXTENDED_LATIN_CAP_FORMS = {
    "Æ": AE_from_H_O,
    "Ø": Oslash_from_O,
}
