from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("z", group="lc")
def z(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420)) * 0.85
    lsb = float(system.tokens.get("lsb_lc", 28))
    pts = [system.map_xy(x, y) for x, y in [
        (lsb, xh), (lsb + w, xh), (lsb, 0), (lsb + w, 0),
    ]]
    return draft_stroke(system, Stroke.through(pts, tension=0.85))
