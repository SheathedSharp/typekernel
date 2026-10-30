"""Round glyph s — gapped top/diag/base (interpolation-safe; open_bowl pair self-intersection)."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System

_GAP = 60.0


@glyph("s", group="lc.round")
def s(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS.get("s", 360.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    gap = _GAP
    top = stroke(system, [(lsb + width * 0.15, xh), (lsb + width * 0.85, xh)], thickness=st)
    diag = stroke(
        system, [(lsb + width * 0.8, xh - gap), (lsb + width * 0.2, gap)], thickness=st
    )
    bot = stroke(system, [(lsb + width * 0.15, 0.0), (lsb + width * 0.85, 0.0)], thickness=st)
    return top + diag + bot
