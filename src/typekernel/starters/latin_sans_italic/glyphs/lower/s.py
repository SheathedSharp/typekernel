"""Round s — three horizontal bars (interpolation-safe; z-diag self-intersection under slant)."""

from __future__ import annotations

from elements import WIDTHS, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("s", group="lc.round")
def s(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(WIDTHS.get("s", 380.0))
    lsb = float(system.tokens["lsb_lc"])
    top = stroke(system, [(lsb + width * 0.12, xh), (lsb + width * 0.88, xh)], thickness=st)
    mid = stroke(
        system, [(lsb + width * 0.2, xh * 0.5), (lsb + width * 0.8, xh * 0.5)], thickness=st
    )
    bot = stroke(system, [(lsb + width * 0.12, 0.0), (lsb + width * 0.88, 0.0)], thickness=st)
    return top + mid + bot
