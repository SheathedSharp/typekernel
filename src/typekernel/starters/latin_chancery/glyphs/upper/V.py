"""V — continuous chevron (G-class)."""

from __future__ import annotations

from elements import fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("V", group="uc.diag")
def V(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("V_width", 620.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.3
    x1 = lsb + width - uc * 0.3
    mid = (x0 + x1) / 2.0
    # Shallow apex (not baseline) reduces SI under slant expand.
    return fuse(stroke(system, [(x0, cap), (mid, cap * 0.12), (x1, cap)], thickness=uc))
