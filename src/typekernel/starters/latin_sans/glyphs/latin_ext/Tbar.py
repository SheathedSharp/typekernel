"""Tbar / tbar — T/t with stroke ."""
from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("Tbar", unicodes=(0x0166,), group="uc.straight")
def Tbar(system: System):
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap); lsb = float(system.tokens.get("lsb_uc", 50.0))
    width = float(WIDTHS.get("T", 620))
    bar = crossbar(lsb, lsb + width, cap - thin / 2, thick=thin, name="bar.t", ends="none")
    mid = stem(lsb + (width - st) / 2, lsb + (width + st) / 2, 0.0, cap - thin * 0.5, name="stem")
    stroke = crossbar(lsb + width * 0.25, lsb + width * 0.75, cap * 0.45, thick=thin * 0.85, name="bar.stroke", ends="none")
    return zone_anchors(bar + mid + stroke, system, top="cap")

@glyph("tbar", unicodes=(0x0167,), group="lc.mixed")
def tbar(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)); width = float(WIDTHS.get("t", 300))
    x0 = lsb + (width - st) / 2
    body = stem(x0, x0 + st, 0.0, asc * 0.85, name="stem")
    bar = crossbar(lsb, lsb + width, xh * 0.85, thick=thin, name="bar", ends="none")
    stroke = crossbar(lsb + width * 0.15, lsb + width * 0.85, xh * 0.45, thick=thin * 0.8, name="bar.stroke", ends="none")
    return zone_anchors(body + bar + stroke, system, top="x")
