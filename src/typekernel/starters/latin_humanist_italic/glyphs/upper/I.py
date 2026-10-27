"""I — single capital stem (skeleton+pen)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("I", group="uc.straight")
def I(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x = lsb + uc * 0.5
    return stroke(system, [(x, 0.0), (x, cap)], thickness=uc)
