"""Ldot / ldot — L/l with middot ."""
from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossbar, dot, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("Ldot", unicodes=(0x013F,), group="uc.straight")
def Ldot(system: System):
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap); lsb = float(system.tokens.get("lsb_uc", 50.0))
    width = float(WIDTHS.get("L", 520))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    bar = crossbar(lsb, lsb + width, thin / 2, thick=thin, name="bar.b", ends="none")
    tittle = dot((lsb + width * 0.72, cap * 0.45), st * 0.9, name="dot")
    return zone_anchors(left + bar + tittle, system, top="cap")

@glyph("ldot", unicodes=(0x0140,), group="lc.straight")
def ldot(system: System):
    st = float(system.stem["lc"]); asc = float(system.zones.asc); xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0)); width = float(WIDTHS.get("l", 180))
    x0 = lsb + (width - st) / 2
    body = stem(x0, x0 + st, 0.0, asc * 0.95, name="stem")
    tittle = dot((x0 + st * 1.6, xh * 0.55), st * 0.85, name="dot")
    return zone_anchors(body + tittle, system, top="x")
