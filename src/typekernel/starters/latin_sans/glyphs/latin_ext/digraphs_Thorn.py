"""Thorn / thorn (P4-2)."""
from __future__ import annotations
from elements import WIDTHS, zone_anchors
from typekernel.anatomy import bowl, stem
from typekernel.project import glyph
from typekernel.system import System

@glyph("Thorn", unicodes=(0x00DE,), group="uc.mixed")
def Thorn(system: System):
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap); lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round); exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("P", 580))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    cy = cap * 0.58; rx = (width - st) * 0.55; cx = lsb + st + rx * 0.85
    ring = bowl((cx, cy), rx, cap * 0.32, thick=st, thin=thin, exponent=exp, overshoot=ov * 0.3, name="bowl")
    return zone_anchors(left + ring, system, top="cap")

@glyph("thorn", unicodes=(0x00FE,), group="lc.mixed")
def thorn(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); asc = float(system.zones.asc); desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)); ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); width = float(WIDTHS.get("b", 430))
    left = stem(lsb, lsb + st, desc * 0.15, asc * 0.95, name="stem.l")
    cx = lsb + st + (width - st) * 0.45; cy = xh * 0.5
    ring = bowl((cx, cy), (width - st) * 0.55, xh * 0.48, thick=st, thin=thin, exponent=exp, overshoot=ov * 0.4, name="bowl")
    return zone_anchors(left + ring, system, top="x")
