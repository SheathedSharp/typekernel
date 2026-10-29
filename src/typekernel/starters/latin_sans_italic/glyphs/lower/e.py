"""Control e — open C + floating crossbar (G-class; keeps aperture)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 70.0


@glyph("e", group="control")
def e(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85)) * 0.65
    xh = float(system.zones.x)
    width = float(system.tokens["o_width"]) * 0.98
    lsb = float(system.tokens["lsb_lc"])
    gap = _GAP
    x = lsb + width * 0.28
    stem = stroke(system, [(x, st * 0.4 + gap), (x, xh - st * 0.4 - gap)], thickness=st)
    top = stroke(
        system, [(x + gap * 0.6, xh - st * 0.35), (lsb + width * 0.82, xh - st * 0.35)], thickness=st
    )
    bot = stroke(
        system, [(x + gap * 0.6, st * 0.35), (lsb + width * 0.82, st * 0.35)], thickness=st
    )
    bar = stroke(
        system, [(lsb + width * 0.45, xh * 0.5), (lsb + width * 0.7, xh * 0.5)], thickness=thin
    )
    return stem + top + bot + bar
