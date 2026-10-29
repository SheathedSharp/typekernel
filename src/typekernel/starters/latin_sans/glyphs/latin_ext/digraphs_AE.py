"""AE / ae digraphs . Paired file — macOS case-insensitive FS."""
from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import BarSpec, bowl, crossbar, diagonal_pair, open_bowl, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("AE", unicodes=(0x00C6,), group="uc.mixed")
def AE(system: System):
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap); lsb = float(system.tokens.get("lsb_uc", 50.0))
    width = float(WIDTHS.get("AE", 920))
    apex = (lsb + width * 0.28, cap)
    left_foot = (lsb + st * 0.2, 0.0); mid = (lsb + width * 0.42, 0.0)
    legs = diagonal_pair(apex, left_foot, mid, weight=st, name="diag")
    right = stem(lsb + width - st, lsb + width, 0.0, cap, name="stem.r")
    top = crossbar(lsb + width * 0.42, lsb + width, cap - thin / 2, thick=thin, name="bar.t", ends="none")
    midb = crossbar(lsb + width * 0.42, lsb + width - st * 0.15, cap * 0.52, thick=thin, name="bar.1", ends="none")
    return zone_anchors(legs + right + top + midb, system, top="cap")

@glyph("ae", unicodes=(0x00E6,), group="lc.mixed")
def ae(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round); exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("ae", 700))
    stem_x0 = lsb + width * 0.42
    right_stem = stem(stem_x0, stem_x0 + st, 0.0, xh, name="stem")
    cx_l = lsb + (stem_x0 - lsb) * 0.55
    left = bowl((cx_l, xh * 0.48), (stem_x0 - lsb) * 0.55, xh * 0.48, thick=st, thin=thin, exponent=exp, overshoot=ov * 0.4, name="bowl.l")
    cx_r = stem_x0 + st + (lsb + width - stem_x0 - st) * 0.5
    rx = (lsb + width - stem_x0 - st) * 0.5
    right = open_bowl((cx_r, xh / 2), rx, xh / 2, thick=st, thin=thin, aperture=0.42, open_side="right", exponent=exp, overshoot=ov, bar=BarSpec(y=xh * 0.52, thick=thin), name="bowl.r")
    return zone_anchors(left + right_stem + right, system, top="x")
