"""c — open bracket strokes with corner gaps (interpolation-safe)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 70.0


@glyph("c", group="lc.round")
def c(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 420.0)) * 0.95
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    gap = _GAP
    x = lsb + width * 0.28
    stem = stroke(system, [(x, st * 0.4 + gap), (x, xh - st * 0.4 - gap)], thickness=st)
    top = stroke(
        system, [(x + gap * 0.6, xh - st * 0.35), (lsb + width * 0.82, xh - st * 0.35)], thickness=st
    )
    bot = stroke(
        system, [(x + gap * 0.6, st * 0.35), (lsb + width * 0.82, st * 0.35)], thickness=st
    )
    return stem + top + bot
