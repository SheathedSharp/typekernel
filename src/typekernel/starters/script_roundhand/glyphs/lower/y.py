from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("y", group="lc")
def y(system: System):
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    w = float(system.tokens.get("n_width", 420)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 28))
    pts = [system.map_xy(x, y) for x, y in [
        (lsb, xh), (lsb + w * 0.45, 0), (lsb + w, xh),
        (lsb + w * 0.55, desc * 0.5), (lsb + w * 0.2, desc),
    ]]
    return draft_stroke(system, Stroke.through(pts, tension=1.0))
