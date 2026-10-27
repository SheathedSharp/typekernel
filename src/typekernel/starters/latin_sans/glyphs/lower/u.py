"""n-group glyph u — two stems + bottom cup trough."""

from __future__ import annotations

from elements import arch_span, stem_rect

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("u", group="lc.straight")
def u(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("u_width", system.tokens["n_width"]))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    inset = st * 0.35
    ov = float(system.overshoot.round) * 0.35
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    left = stem_rect(lsb, lsb + st, 0.0, xh, prefix="stem.l")
    right = stem_rect(lsb + width - st, lsb + width, 0.0, xh, prefix="stem.r")
    x_l, x_r = lsb + inset, lsb + width - inset
    y_outer = -ov
    y_inner = st - ov * 0.5
    outer = arch_span(x_l, y_outer, x_r, y_outer, y_outer - 8.0, tension=tension)
    inner = arch_span(x_r, y_inner, x_l, y_inner, y_inner + 6.0, tension=tension)
    cup = (
        Writer()
        .start((x_l, y_inner))
        .corner("cup.l.inner")
        .line((x_l, y_outer))
        .corner("cup.l.outer")
        .fragment(outer)
        .corner("cup.r.outer")
        .line((x_r, y_inner))
        .corner("cup.r.inner")
        .fragment(inner)
        .close()
        .build()
    )
    return left + right + cup
