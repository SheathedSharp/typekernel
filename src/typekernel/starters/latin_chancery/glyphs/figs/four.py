"""Figure 4 — open triangle + stem."""
from __future__ import annotations
from elements import stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("four", group="figs")
def four(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    x_stem = lsb + width * 0.62
    stem = stroke(system, [(x_stem, 0.0), (x_stem, h)], thickness=st)
    arm = stroke(system, [(lsb + st * 0.3, h * 0.38), (x_stem + st * 0.8, h * 0.38)], thickness=st)
    diag = stroke(system, [(lsb + st * 0.4, h * 0.38), (x_stem - st * 0.2, h)], thickness=st)
    return stem + arm + diag
