"""Lowercase l — ascender stem with exit flourish."""
from __future__ import annotations

from elements import flourish_exit, stroke, stroke_fragment

from typekernel.project import glyph
from typekernel.system import System


@glyph("l", group="lc.straight")
def l(system: System):
    st = float(system.stem["lc"])
    asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x = lsb + st * 0.5
    stem = stroke(system, [(x, 0.0), (x, asc - 40.0)], thickness=st)
    tip = (x - 70.0, asc + 20.0)
    frag = flourish_exit(system, x, asc - 40.0, tip)
    return stem + stroke_fragment(system, frag, thickness=float(system.stem["lc_h"]))
