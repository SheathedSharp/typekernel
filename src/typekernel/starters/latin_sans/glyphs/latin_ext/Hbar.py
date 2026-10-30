"""Hbar / hbar — H/h with stroke ."""
from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import arch, crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("Hbar", unicodes=(0x0126,), group="uc.straight")
def Hbar(system: System):
    st = float(system.stem["uc"]); thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap); lsb = float(system.tokens.get("lsb_uc", 50.0))
    width = float(system.tokens.get("H_width", WIDTHS.get("H", 700)))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    right = stem(lsb + width - st, lsb + width, 0.0, cap, name="stem.r")
    bar = crossbar(lsb, lsb + width, cap * 0.5, thick=thin, name="bar", ends="none")
    stroke = crossbar(lsb - st * 0.4, lsb + width + st * 0.4, cap * 0.72, thick=thin * 0.9, name="bar.1", ends="none")
    return zone_anchors(left + right + bar + stroke, system, top="cap")

@glyph("hbar", unicodes=(0x0127,), group="lc.straight")
def hbar(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 40.0)); width = float(WIDTHS.get("h", 430))
    left = stem(lsb, lsb + st, 0.0, asc * 0.95, name="stem.l")
    right = stem(lsb + width - st, lsb + width, 0.0, xh, name="stem.r")
    shoulder = arch(lsb + st, lsb + width - st, height=xh, thick=st, thin=thin, join_depth=st * 0.55, tension=0.55, name="arch")
    # High ascender stroke — avoid kissing the arch (Bold slit counters).
    stroke = crossbar(
        lsb - st * 0.25,
        lsb + st * 1.45,
        asc * 0.84,
        thick=thin * 0.85,
        name="bar.1",
        ends="none",
    )
    return zone_anchors(left + right + shoulder + stroke, system, top="x")
