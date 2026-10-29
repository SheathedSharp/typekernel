"""Straight glyph I — anatomy capital stem (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("I", group="uc.straight")
def glyph_I(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["I"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    x0 = lsb + (width - uc) / 2.0
    return zone_anchors(stem(x0, x0 + uc, 0.0, cap, name="stem"), system, top='cap', ogonek=True)
