"""Figure 1 — stem + flag."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("one", group="figs")
def one(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 420.0)) * 0.55
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    x = lsb + width * 0.55
    stem = stroke(system, [(x, 0.0), (x, h)], thickness=st)
    flag = stroke(system, [(x - st * 1.4, h * 0.78), (x, h)], thickness=st * 0.85)
    base = stroke(
        system, [(x - st * 1.2, 0.0), (x + st * 1.2, 0.0)],
        thickness=float(system.stem["lc_h"]),
    )
    return stem + flag + base
