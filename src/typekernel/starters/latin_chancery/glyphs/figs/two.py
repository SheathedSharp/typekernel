"""Figure 2 — open top + diagonal + base."""
from __future__ import annotations

from elements import open_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("two", group="figs")
def two(system: System):
    st = float(system.stem["lc"])
    width = float(system.tokens.get("fig_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    h = float(system.zones.cap) * 0.72
    cx = lsb + width / 2.0
    top = open_bowl(
        system, cx=cx, cy=h * 0.68, rx=width * 0.38, ry=h * 0.28,
        thickness=st, open_side="left", aperture_deg=100.0,
    )
    diag = stroke(system, [(cx + width * 0.32, h * 0.55), (lsb + st * 0.3, 0.0)], thickness=st)
    base = stroke(
        system, [(lsb + st * 0.2, 0.0), (lsb + width - st * 0.2, 0.0)],
        thickness=float(system.stem["lc_h"]),
    )
    return top + diag + base
