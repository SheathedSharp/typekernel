"""UC I — single stem."""

from __future__ import annotations

from elements import WIDTHS, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("I", group="uc.straight")
def I(system: System):
    st = float(system.stem["uc"])
    width = float(WIDTHS.get("I", 220.0))
    lsb = float(system.tokens["lsb_uc"])
    return uc_stem(system, lsb + width / 2.0, thickness=st)
