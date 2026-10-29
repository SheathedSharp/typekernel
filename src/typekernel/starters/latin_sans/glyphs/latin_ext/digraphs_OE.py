"""OE / oe digraphs ."""
from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import BarSpec, bowl, crossbar, open_bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("OE", unicodes=(0x0152,), group="uc.round")
def OE(system: System):
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap); lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round); exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("OE", 980))
    bowl_w = width * 0.58
    ring = bowl((lsb + bowl_w / 2, cap / 2), bowl_w / 2, cap / 2, thick=st, thin=thin, exponent=exp, overshoot=ov, name="bowl")
    right = stem(lsb + width - st, lsb + width, 0.0, cap, name="stem.r")
    top = crossbar(lsb + bowl_w * 0.55, lsb + width, cap - thin / 2, thick=thin, name="bar.t", ends="none")
    mid = crossbar(lsb + bowl_w * 0.55, lsb + width - st * 0.2, cap * 0.5, thick=thin, name="bar.1", ends="none")
    bot = crossbar(lsb + bowl_w * 0.55, lsb + width, thin / 2, thick=thin, name="bar.b", ends="none")
    return zone_anchors(ring + right + top + mid + bot, system, top="cap")

@glyph("oe", unicodes=(0x0153,), group="lc.round")
def oe(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round); exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("oe", 720))
    left_w = width * 0.52
    left = bowl((lsb + left_w / 2, xh / 2), left_w / 2, xh / 2, thick=st, thin=thin, exponent=exp, overshoot=ov, name="bowl.l")
    rx = (width - left_w) * 0.5
    cx = lsb + left_w + rx
    right = open_bowl((cx, xh / 2), rx, xh / 2, thick=st, thin=thin, aperture=0.4, open_side="right", exponent=exp, overshoot=ov, bar=BarSpec(y=xh * 0.52, thick=thin), name="bowl.r")
    return zone_anchors(left + right, system, top="x")
