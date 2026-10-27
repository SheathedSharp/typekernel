"""o-group glyph q — slanted stem + nestled oval bowl (skeleton+pen)."""

from __future__ import annotations

from elements import nest_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("q", group="lc.bowl")
def q(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("o_width", 420.0))
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x_stem = lsb + width - st * 0.5
    stem_d = stroke(system, [(x_stem, desc), (x_stem, xh)], thickness=st)
    bowl = nest_bowl(system, stem_x=x_stem, side="left", width=width, xh=xh, lsb=lsb)
    return stem_d + bowl
