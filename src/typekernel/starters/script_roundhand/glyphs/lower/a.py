from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("a", group="lc")
def a(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420)) * 0.85
    lsb = float(system.tokens.get("lsb_lc", 28))
    pts = [system.map_xy(x, y) for x, y in [
        (lsb + w * 0.75, xh * 0.55),
        (lsb + w * 0.15, xh * 0.75),
        (lsb + w * 0.2, xh * 0.2),
        (lsb + w * 0.75, 0),
        (lsb + w * 0.85, xh),
    ]]
    return draft_stroke(system, Stroke.through(pts, tension=1.0), anchors={
        "entry": (*pts[0], 0.0, float(system.stem["lc_h"])),
        "exit": (*pts[-1], -90.0, float(system.stem["lc"])),
    })
