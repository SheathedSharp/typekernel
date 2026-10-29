"""kgreenlandic — small-cap k form ."""
from __future__ import annotations
from elements import WIDTHS, zone_anchors
from typekernel.anatomy import diagonal_pair, stem
from typekernel.project import glyph
from typekernel.system import System

@glyph("kgreenlandic", unicodes=(0x0138,), group="lc.mixed")
def kgreenlandic(system: System):
    st = float(system.stem["lc"]); xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0)); width = float(WIDTHS.get("k", 430))
    left = stem(lsb, lsb + st, 0.0, xh, name="stem.l")
    arms = diagonal_pair((lsb + st * 0.7, xh * 0.52), (lsb + width, xh), (lsb + width, 0.0), weight=st * 0.9, name="diag")
    return zone_anchors(left + arms, system, top="x")
