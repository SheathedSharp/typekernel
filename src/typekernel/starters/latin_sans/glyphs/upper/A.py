"""Diagonal glyph A — anatomy diagonal_pair + crossbar (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import crossbar, diagonal_pair
from typekernel.project import glyph
from typekernel.system import System


@glyph("A", group="uc.diagonal")
def glyph_A(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS["A"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    cx = lsb + width / 2.0
    legs = diagonal_pair(
        (cx, cap),
        (lsb + st * 0.25, 0.0),
        (lsb + width - st * 0.25, 0.0),
        weight=st,
        name="diag",
    )
    bar = crossbar(
        lsb + width * 0.22,
        lsb + width * 0.78,
        cap * 0.38,
        thick=thin,
        name="bar",
        ends="none",
    )
    return zone_anchors(legs + bar, system, top='cap', ogonek=True)
