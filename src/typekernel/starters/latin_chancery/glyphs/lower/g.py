"""Lowercase g — bowl + descender loop (open)."""
from __future__ import annotations
from elements import nest_bowl, open_bowl, stroke
from typekernel.project import glyph
from typekernel.system import System

@glyph("g", group="lc.round")
def g(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(system.tokens.get("o_width", 400.0))
    lsb = float(system.tokens.get("lsb_lc", 32.0))
    x_stem = lsb + width - st * 0.5
    stem_d = stroke(system, [(x_stem, xh), (x_stem, desc + 40.0)], thickness=st)
    upper = nest_bowl(system, stem_x=x_stem, side="left", width=width, xh=xh, lsb=lsb)
    loop = open_bowl(
        system,
        cx=lsb + width * 0.45,
        cy=desc * 0.45,
        rx=width * 0.38,
        ry=abs(desc) * 0.42,
        thickness=st,
        open_side="right",
        aperture_deg=70.0,
    )
    return upper + stem_d + loop
