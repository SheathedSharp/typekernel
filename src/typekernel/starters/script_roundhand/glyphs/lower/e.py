from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("e", group="lc")
def e(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("o_width", 440)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 28))
    pts = [system.map_xy(x, y) for x, y in [
        (lsb + w * 0.2, xh * 0.55),
        (lsb + w * 0.85, xh * 0.7),
        (lsb + w * 0.55, xh),
        (lsb + w * 0.15, xh * 0.55),
        (lsb + w * 0.25, 0.0),
        (lsb + w * 0.8, 0.05),
    ]]
    return draft_stroke(system, Stroke.through(pts, tension=1.1), pressure=False)
