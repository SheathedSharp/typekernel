"""A — continuous inverted-V skeleton + crossbar (shared stroke)."""

from __future__ import annotations

from elements import stroke

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
    # One continuous diagonal rail through the apex (no separate join heal).
    body = stroke(system, [(x0, 0.0), (apex, cap), (x1, 0.0)], thickness=uc)
    bar_y = cap * 0.38
    t = bar_y / cap
    xl = x0 + (apex - x0) * t
    xr = x1 + (apex - x1) * t
    bar = stroke(system, [(xl, bar_y), (xr, bar_y)], thickness=uc * 0.85)
    return body + bar
