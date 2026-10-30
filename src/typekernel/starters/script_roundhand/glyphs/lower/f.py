from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("f", group="lc")
def f(system: System):
    asc = float(system.zones.asc)
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 28))
    pts = [system.map_xy(x, y) for x, y in [
        (lsb + 120, asc), (lsb + 40, asc * 0.7), (lsb + 40, 0),
        (lsb + 10, xh * 0.7), (lsb + 130, xh * 0.7),
    ]]
    return draft_stroke(system, Stroke.through(pts, tension=1.0))
