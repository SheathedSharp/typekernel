"""A — per-leg compensated diagonals + crossbar (overlap at apex)."""

from __future__ import annotations

from elements import diagonal_stroke, fuse, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("A", group="uc.diag")
def A(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("A_width", 620.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    x0 = lsb + uc * 0.2
    x1 = lsb + width - uc * 0.2
    apex = (x0 + x1) / 2.0
    # Separate legs so each diagonal self-calibrates under the broad nib.
    left = diagonal_stroke(system, [(x0, 0.0), (apex, cap)], thickness=uc)
    right = diagonal_stroke(system, [(apex, cap), (x1, 0.0)], thickness=uc)
    bar_y = cap * 0.38
    t = bar_y / cap
    xl = x0 + (apex - x0) * t
    xr = x1 + (apex - x1) * t
    bar = stroke(system, [(xl, bar_y), (xr, bar_y)], thickness=uc * 0.85)
    return fuse(left + right + bar)
