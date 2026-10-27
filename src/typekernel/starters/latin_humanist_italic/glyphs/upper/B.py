"""B — stem + continuous double-bowl arc nestled into the stem."""

from __future__ import annotations

from elements import open_arc_points, stroke, uc_stem

from typekernel.project import glyph
from typekernel.system import System


@glyph("B", group="uc.round")
def B(system: System):
    uc = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens.get("B_width", 560.0))
    lsb = float(system.tokens.get("lsb_uc", 44.0))
    ov = float(system.overshoot.round)
    x0 = lsb + uc * 0.5
    stem = uc_stem(system, x0, thickness=uc)
    # Both arcs open toward the stem: terminals at ~±120° (near stem), belly east.
    rx_u = width * 0.40
    rx_l = width * 0.44
    cy_u = cap * 0.70
    cy_l = cap * 0.30
    ry_u = cap * 0.28 + ov * 0.2
    ry_l = cap * 0.30 + ov * 0.2
    pull = 0.38
    upper = open_arc_points(
        x0 + rx_u * pull, cy_u, rx_u, ry_u, start_deg=125.0, end_deg=-125.0, n=20
    )
    lower = open_arc_points(
        x0 + rx_l * pull, cy_l, rx_l, ry_l, start_deg=125.0, end_deg=-125.0, n=20
    )
    # Continuous: upper then lower (waist terminals sit on the stem).
    bowls = stroke(system, list(upper) + list(lower), thickness=uc)
    return stem + bowls
