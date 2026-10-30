"""E — continuous top/stem/bottom rail + mid bar (shared uc_stem join)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("E", group="uc.straight")
def E(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("E", 500.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x = lsb + uc * 0.5
    x1 = lsb + width
    # Continuous C-rail: top bar → stem → bottom bar (joins share endpoints).
    rail = stroke(
        system,
        [(x1, cap), (x, cap), (x, 0.0), (x1, 0.0)],
        thickness=uc,
    )
    mid = stroke(
        system,
        [(x, cap * 0.5), (lsb + width * 0.85, cap * 0.5)],
        thickness=uc * 0.85,
    )
    return fuse(rail + mid)
