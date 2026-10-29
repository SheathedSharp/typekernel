"""Mixed glyph U — anatomy stems + bottom cup (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, arch_span

from typekernel.anatomy import stem
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("U", group="uc.mixed")
def glyph_U(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["U"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    left = stem(lsb, lsb + st, st * 0.9, cap, name="stem.l", foot="none")
    right = stem(lsb + width - st, lsb + width, st * 0.9, cap, name="stem.r", foot="none")
    x_l, x_r = lsb + st * 0.35, lsb + width - st * 0.35
    y_outer, y_inner = -ov, st * 0.95
    outer = arch_span(x_l, y_outer, x_r, y_outer, y_outer - 10.0, tension=tension)
    inner = arch_span(x_r, y_inner, x_l, y_inner, y_inner + 8.0, tension=tension)
    cup = (
        Writer()
        .start((x_l, y_inner))
        .corner("arch.l.i")
        .line((x_l, y_outer))
        .corner("arch.l.o")
        .fragment(outer)
        .corner("arch.r.o")
        .line((x_r, y_inner))
        .corner("arch.r.i")
        .fragment(inner)
        .close()
        .build()
    )
    return left + right + cup
