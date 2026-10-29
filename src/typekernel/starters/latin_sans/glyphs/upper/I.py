"""H-group glyph I — single capital stem."""

from __future__ import annotations

from elements import WIDTHS, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("I", group="uc.straight")
def glyph_I(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["I"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    x0 = lsb + (width - uc) / 2.0
    return stem_rect(x0, x0 + uc, 0.0, cap, prefix="stem")
