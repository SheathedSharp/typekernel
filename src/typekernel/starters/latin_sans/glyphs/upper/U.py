"""Rest glyph U — two stems + bottom cup."""

from __future__ import annotations

from elements import WIDTHS, arch_span, stem_rect

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("U", group="uc.straight")
def glyph_U(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["U"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    left = stem_rect(lsb, lsb + st, st * 0.9, cap, prefix="stem.l")
    right = stem_rect(lsb + width - st, lsb + width, st * 0.9, cap, prefix="stem.r")
    x_l, x_r = lsb + st * 0.35, lsb + width - st * 0.35
    y_outer, y_inner = -ov, st * 0.95
    outer = arch_span(x_l, y_outer, x_r, y_outer, y_outer - 10.0, tension=tension)
    inner = arch_span(x_r, y_inner, x_l, y_inner, y_inner + 8.0, tension=tension)
    cup = (
        Writer()
        .start((x_l, y_inner))
        .corner("U.cup.l.i")
        .line((x_l, y_outer))
        .corner("U.cup.l.o")
        .fragment(outer)
        .corner("U.cup.r.o")
        .line((x_r, y_inner))
        .corner("U.cup.r.i")
        .fragment(inner)
        .close()
        .build()
    )
    return left + right + cup
