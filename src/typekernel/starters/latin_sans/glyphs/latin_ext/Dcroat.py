"""Dcroat / dcroat — D/d with stroke ."""
from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("Dcroat", unicodes=(0x0110,), group="uc.round")
def Dcroat(system: System):
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap); lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round); exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("D", 680))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    ring = bowl((lsb + width * 0.55, cap / 2), width * 0.42, cap / 2, thick=st, thin=thin, exponent=exp, overshoot=ov, name="bowl")
    stroke = crossbar(lsb - st * 0.35, lsb + st * 1.8, cap * 0.55, thick=thin, name="bar.stroke", ends="none")
    return zone_anchors(left + ring + stroke, system, top="cap")

@glyph("dcroat", unicodes=(0x0111,), group="lc.round")
def dcroat(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)); ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); width = float(WIDTHS.get("d", 430))
    right = stem(lsb + width - st, lsb + width, 0.0, asc * 0.95, name="stem.r")
    cx = lsb + (width - st) * 0.5
    ring = bowl((cx, xh * 0.48), (width - st) * 0.55, xh * 0.48, thick=st, thin=thin, exponent=exp, overshoot=ov * 0.5, name="bowl")
    stroke = crossbar(lsb + width - st * 1.8, lsb + width + st * 0.35, asc * 0.7, thick=thin * 0.85, name="bar.stroke", ends="none")
    return zone_anchors(ring + right + stroke, system, top="x")
