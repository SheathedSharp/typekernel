"""U — stems + shallow cup (G-class; deep U SI under slant)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("U", group="uc.straight")
def U(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("U_width", 620.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + st * 0.5
    x1 = lsb + width - st * 0.5
    cup = cap * 0.22
    return fuse(
        stroke(system, [(x0, cap), (x0, cup), (x1, cup), (x1, cap)], thickness=st)
    )
