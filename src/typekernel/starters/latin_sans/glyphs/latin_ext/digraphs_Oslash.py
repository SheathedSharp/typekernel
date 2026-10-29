"""Oslash / oslash ."""
from __future__ import annotations

from elements import zone_anchors

from typekernel.anatomy import bowl
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


@glyph("Oslash", unicodes=(0x00D8,), group="uc.round")
def Oslash(system: System):
    width = float(system.tokens["O_width"]); lsb = float(system.tokens.get("lsb_uc", 50.0))
    cap = float(system.zones.cap); ov = float(system.overshoot.round)
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    cx = lsb + width / 2; cy = cap / 2
    ring = bowl((cx, cy), width / 2, cap / 2, thick=st, thin=thin, exponent=exp, overshoot=ov, name="bowl")
    left, right = diagonal_band((lsb + width * 0.85, cap * 0.92), (lsb + width * 0.15, cap * 0.08), weight=st * 0.85, compensate=True)
    stroke = (Writer().start(left.start).corner("diag.t.l").fragment(left).corner("diag.b.l")
              .line(right.start).corner("diag.b.r").fragment(right).corner("diag.t.r").line(left.start).close().build())
    return zone_anchors(ring + stroke, system, top="cap")

@glyph("oslash", unicodes=(0x00F8,), group="lc.round")
def oslash(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round); exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(system.tokens.get("o_width", 450))
    cx = lsb + width / 2; cy = xh / 2
    ring = bowl((cx, cy), width / 2, xh / 2, thick=st, thin=thin, exponent=exp, overshoot=ov, name="bowl")
    left, right = diagonal_band((lsb + width * 0.88, xh * 0.95), (lsb + width * 0.12, xh * 0.05), weight=st * 0.8, compensate=True)
    stroke = (Writer().start(left.start).corner("diag.t.l").fragment(left).corner("diag.b.l")
              .line(right.start).corner("diag.b.r").fragment(right).corner("diag.t.r").line(left.start).close().build())
    return zone_anchors(ring + stroke, system, top="x")
