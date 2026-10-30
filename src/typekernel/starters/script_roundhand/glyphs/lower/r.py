from elements import Stroke, draft_stroke, join_anchors, join_y

from typekernel.project import glyph
from typekernel.system import System


@glyph("r", group="lc")
def r(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420)) * 0.55
    lsb = float(system.tokens.get("lsb_lc", 28))
    jy = join_y(system)
    x0 = lsb + 40
    pts = [
        system.map_xy(x, y)
        for x, y in [
            (x0, jy),
            (x0, xh),
            (x0 + w * 0.35, xh * 0.85),
            (lsb + w, xh * 0.75),
        ]
    ]
    return draft_stroke(
        system,
        Stroke.through(pts, tension=1.0),
        anchors=join_anchors(system, (x0, jy), (lsb + w, jy)),
        pressure=False,
    )
