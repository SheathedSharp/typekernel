"""Control glyph o — slanted oval bowl."""
from __future__ import annotations

from elements import bowl

from typekernel.project import glyph
from typekernel.system import System


@glyph("o", group="control")
def o(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["o_width"])
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    ov = float(system.overshoot.round)
    return bowl(
        system,
        cx=lsb + width * 0.5,
        cy=xh * 0.5,
        rx=width * 0.5 - st * 0.15,
        ry=xh * 0.5 + ov - st * 0.1,
        thickness=st,
    )
