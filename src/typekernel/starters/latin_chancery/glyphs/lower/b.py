"""Lowercase b — ascender stem + nestled bowl."""
from __future__ import annotations

from elements import flourish_exit, nest_bowl, stroke, stroke_fragment

from typekernel.project import glyph
from typekernel.system import System


@glyph("b", group="lc.bowl")
def b(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(system.tokens.get("o_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x_stem = lsb + st * 0.5
    stem_d = stroke(system, [(x_stem, 0.0), (x_stem, asc - 40.0)], thickness=st)
    bowl = nest_bowl(system, stem_x=x_stem, side="right", width=width, xh=xh, lsb=lsb)
    tip = (x_stem - 70.0, asc + 20.0)
    frag = flourish_exit(system, x_stem, asc - 40.0, tip)
    return stem_d + bowl + stroke_fragment(system, frag, thickness=float(system.stem["lc_h"]))
