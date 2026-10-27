"""o-group glyph a — nestled bowl + right stem (skeleton+pen)."""

from __future__ import annotations

from elements import nest_bowl, stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("a", group="lc.bowl")
def a(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens.get("o_width", 420.0)) * 0.95
    lsb = float(system.tokens.get("lsb_lc", 36.0))
    x_stem = lsb + width - st * 0.5
    stem_d = stroke(system, [(x_stem, 0.0), (x_stem, xh)], thickness=st)
    bowl = nest_bowl(system, stem_x=x_stem, side="left", width=width, xh=xh, lsb=lsb)
    return stem_d + bowl
