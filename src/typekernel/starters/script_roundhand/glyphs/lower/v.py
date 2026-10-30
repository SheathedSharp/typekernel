from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("v", group="lc")
def v(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 28))
    pts = [system.map_xy(x, y) for x, y in [
        (lsb, xh), (lsb + w * 0.5, 0), (lsb + w, xh),
    ]]
    return draft_stroke(system, Stroke.through(pts, tension=0.95))
