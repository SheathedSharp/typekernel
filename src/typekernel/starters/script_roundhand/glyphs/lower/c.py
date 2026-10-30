import math

from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("c", group="lc")
def c(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("o_width", 440)) * 0.85
    lsb = float(system.tokens.get("lsb_lc", 28))
    cx, cy, rx, ry = lsb + w * 0.5, xh * 0.5, w * 0.38, xh * 0.48
    pts = []
    for i in range(7):
        ang = math.radians(40 + 260 * i / 6)
        pts.append(system.map_xy(cx + rx * math.cos(ang), cy + ry * math.sin(ang)))
    return draft_stroke(system, Stroke.through(pts, tension=1.05))
