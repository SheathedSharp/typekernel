from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("r", group="lc")
def r(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420)) * 0.55
    lsb = float(system.tokens.get("lsb_lc", 28))
    pts = [system.map_xy(x, y) for x, y in [
        (lsb + 40, xh), (lsb + 40, 0), (lsb + w * 0.3, xh * 0.7), (lsb + w, xh * 0.85),
    ]]
    return draft_stroke(system, Stroke.through(pts, tension=1.0))
