"""n-group glyph h — ascender stem + n shoulder."""

from __future__ import annotations

from elements import shoulder_trough, stem_rect

from typekernel.project import glyph
from typekernel.system import System


@glyph("h", group="lc.straight")
def h(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    width = float(system.tokens.get("h_width", system.tokens["n_width"]))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    inset = st * 0.35
    left = stem_rect(lsb, lsb + st, 0.0, asc, prefix="stem.l")
    right = stem_rect(lsb + width - st, lsb + width, 0.0, xh, prefix="stem.r")
    trough = shoulder_trough(
        system,
        x_left=lsb + inset,
        x_right=lsb + width - inset,
        y_top=xh,
        y_bot=xh - st + float(system.overshoot.round) * 0.35,
        tag_prefix="arch",
    )
    return left + right + trough
