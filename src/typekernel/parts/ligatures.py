"""Common Latin ligatures (fixed topology, no boolean)."""

from __future__ import annotations

from dataclasses import replace

from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    _n_record,
    _pack,
    dotless_i_from_n,
    f_from_n,
    l_from_n,
)

__all__ = ["LIGATURE_FORMS", "fi_from_n", "fl_from_n"]


def fi_from_n(n: ComposedGlyph, _o: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    f = f_from_n(n, c)
    i = dotless_i_from_n(n, c)
    kern = m.stem * 0.42
    i_shift = i.translated(f.advance - kern)
    adv = f.advance + i_shift.advance - kern * 0.55
    g = _pack(c, m, {}, *f.solids, *i_shift.solids)
    return replace(g, advance=adv)


def fl_from_n(n: ComposedGlyph, _o: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    f = f_from_n(n, c)
    ell = l_from_n(n, c)
    kern = m.stem * 0.38
    l_shift = ell.translated(f.advance - kern)
    adv = f.advance + l_shift.advance - kern * 0.5
    g = _pack(c, m, {}, *f.solids, *l_shift.solids)
    return replace(g, advance=adv)


LIGATURE_FORMS = {
    "fi": fi_from_n,
    "fl": fl_from_n,
}
