"""Control glyph H — anatomy stems + crossbar ."""

from __future__ import annotations

from elements import zone_anchors

from typekernel.anatomy import crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("H", group="uc.straight")
def H(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["H_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    bar_t = float(system.tokens.get("bar_thickness", uc * 0.85))
    bar_cy = float(system.tokens.get("bar_height", cap * 0.48))

    left = stem(lsb, lsb + uc, 0.0, cap, name="stem.l")
    right = stem(lsb + width - uc, lsb + width, 0.0, cap, name="stem.r")
    # Bar overlaps both stems (ends=none: no end slots into stem interiors).
    bar = crossbar(
        lsb + uc * 0.5,
        lsb + width - uc * 0.5,
        bar_cy,
        thick=bar_t,
        name="bar",
        ends="none",
    )
    return zone_anchors(left + right + bar, system, top='cap')
