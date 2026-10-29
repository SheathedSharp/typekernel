"""germandbls — long-s + s compound approx (P4-2)."""
from __future__ import annotations
from elements import WIDTHS, zone_anchors
from typekernel.anatomy import open_bowl, stem
from typekernel.project import glyph
from typekernel.system import System

@glyph("germandbls", unicodes=(0x00DF,), group="lc.mixed")
def germandbls(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)); ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); width = float(WIDTHS.get("germandbls", 520))
    left = stem(lsb, lsb + st, 0.0, asc * 0.92, name="stem.l")
    # upper bowl (like b) + lower open s-ish
    cx = lsb + st + (width - st) * 0.42
    upper = open_bowl((cx, asc * 0.62), (width - st) * 0.45, asc * 0.28, thick=st, thin=thin, aperture=0.35, open_side="right", exponent=exp, overshoot=ov * 0.3, name="bowl.t")
    lower = open_bowl((cx, xh * 0.42), (width - st) * 0.48, xh * 0.42, thick=st, thin=thin, aperture=0.4, open_side="left", exponent=exp, overshoot=ov * 0.4, name="bowl.b")
    return zone_anchors(left + upper + lower, system, top="x")
