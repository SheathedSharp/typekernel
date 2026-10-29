"""Lslash / lslash — L/l with diagonal slash (P4-2)."""
from __future__ import annotations
from elements import WIDTHS, zone_anchors
from typekernel.anatomy import crossbar, stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System

@glyph("Lslash", unicodes=(0x0141,), group="uc.straight")
def Lslash(system: System):
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap); lsb = float(system.tokens.get("lsb_uc", 50.0))
    width = float(WIDTHS.get("L", 520))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    bar = crossbar(lsb, lsb + width, thin / 2, thick=thin, name="bar.b", ends="none")
    left_b, right_b = diagonal_band((lsb + width * 0.55, cap * 0.55), (lsb - st * 0.2, cap * 0.25), weight=st * 0.75, compensate=True)
    slash = (Writer().start(left_b.start).corner("slash.t.l").fragment(left_b).corner("slash.b.l")
             .line(right_b.start).corner("slash.b.r").fragment(right_b).corner("slash.t.r").line(left_b.start).close().build())
    return zone_anchors(left + bar + slash, system, top="cap")

@glyph("lslash", unicodes=(0x0142,), group="lc.straight")
def lslash(system: System):
    st = float(system.stem["lc"]); xh = float(system.zones.x); asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)); width = float(WIDTHS.get("l", 180))
    x0 = lsb + (width - st) / 2
    body = stem(x0, x0 + st, 0.0, asc * 0.95, name="stem")
    left_b, right_b = diagonal_band((x0 + st * 1.8, xh * 0.7), (x0 - st * 0.9, xh * 0.25), weight=st * 0.7, compensate=True)
    slash = (Writer().start(left_b.start).corner("slash.t.l").fragment(left_b).corner("slash.b.l")
             .line(right_b.start).corner("slash.b.r").fragment(right_b).corner("slash.t.r").line(left_b.start).close().build())
    return zone_anchors(body + slash, system, top="x")
