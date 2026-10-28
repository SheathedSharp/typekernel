"""Lowercase p — descender stem + nestled bowl."""
from __future__ import annotations

from elements import nest_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("p", group="lc.bowl")
def p(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("o_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x_stem = lsb + st * 0.5
    stem_d = stroke(system, [(x_stem, xh), (x_stem, desc)], thickness=st)
    bowl = nest_bowl(system, stem_x=x_stem, side="right", width=width, xh=xh, lsb=lsb)
    return stem_d + bowl
