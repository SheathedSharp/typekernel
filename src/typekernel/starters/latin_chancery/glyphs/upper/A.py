"""A — near-vertical legs + top + crossbar (interpolation-safe; acute apex self-intersection)."""

from __future__ import annotations

from elements import WIDTHS, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("A", group="uc.diag")
def A(system: System):
    uc = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", uc * 0.85))
    cap = float(system.zones.cap)
    width = float(WIDTHS.get("A", 620.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    inset = 0.12
    x0b = lsb + uc * 0.4
    x1b = lsb + width - uc * 0.4
    x0t = lsb + width * inset + uc * 0.4
    x1t = lsb + width * (1.0 - inset) - uc * 0.4
    bar_y = cap * 0.38
    return fuse(
        stroke(system, [(x0b, 0.0), (x0t, cap)], thickness=uc)
        + stroke(system, [(x1b, 0.0), (x1t, cap)], thickness=uc)
        + stroke(system, [(x0t, cap), (x1t, cap)], thickness=thin)
        + stroke(
            system,
            [(x0b + (x0t - x0b) * 0.4, bar_y), (x1b + (x1t - x1b) * 0.4, bar_y)],
            thickness=thin,
        )
    )
