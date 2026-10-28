"""Control glyph O — slanted oval."""
from __future__ import annotations

from elements import bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("O", group="control")
def O(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(system.tokens["O_width"])
    lsb = float(system.tokens.get("lsb_uc", 40.0))
    ov = float(system.overshoot.round)
    return bowl(
        system,
        cx=lsb + width * 0.5,
        cy=cap * 0.5,
        rx=width * 0.5 - st * 0.1,
        ry=cap * 0.5 + ov - st * 0.05,
        thickness=st,
    )
