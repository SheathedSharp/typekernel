from elements import Stroke, draft_stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("u", group="lc")
def u(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420))
    lsb = float(system.tokens.get("lsb_lc", 28))
    st = float(system.stem["lc"])
    x0, x1 = lsb + st * 0.4, lsb + w - st * 0.4
    pts = [system.map_xy(x, y) for x, y in [
        (x0, xh), (x0, 0), (x0 + (x1 - x0) * 0.5, 0), (x1, 0), (x1, xh),
    ]]
    return draft_stroke(system, Stroke.through(pts, tension=1.0), anchors={
        "entry": (*pts[0], -90.0, float(system.stem["lc"])),
        "exit": (*pts[-1], 90.0, float(system.stem["lc_h"])),
    })
