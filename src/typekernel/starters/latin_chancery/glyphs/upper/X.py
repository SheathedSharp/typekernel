"""X — two mild crossing bars with gap (interpolation-safe)."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("X", group="uc.diag")
def X(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("X_width", 600.0))
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    x0 = lsb + uc * 0.25
    x1 = lsb + width - uc * 0.25
    # Separated diags — fused cross self-intersection under slant.
    gap = 40.0
    mid = (x0 + x1) / 2.0
    return (
        stroke(system, [(x0, cap), (mid - gap, cap * 0.5)], thickness=uc)
        + stroke(system, [(mid + gap, cap * 0.5), (x1, 0.0)], thickness=uc)
        + stroke(system, [(x1, cap), (mid + gap, cap * 0.5)], thickness=uc)
        + stroke(system, [(mid - gap, cap * 0.5), (x0, 0.0)], thickness=uc)
    )
