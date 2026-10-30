from elements import Stroke, draft_stroke, join_anchors, join_y

from typekernel.project import glyph
from typekernel.system import System


@glyph("u", group="lc")
def u(system: System):
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420))
    lsb = float(system.tokens.get("lsb_lc", 28))
    st = float(system.stem["lc"])
    jy = join_y(system)
    x0, x1 = lsb + st * 0.4, lsb + w - st * 0.4
    pts = [
        system.map_xy(x, y)
        for x, y in [
            (x0, jy),
            (x0, xh * 0.15),
            (x0 + (x1 - x0) * 0.5, 0.0),
            (x1, xh * 0.15),
            (x1, jy),
        ]
    ]
    return draft_stroke(
        system,
        Stroke.through(pts, tension=1.0),
        anchors=join_anchors(system, (x0, jy), (x1, jy)),
        pressure=False,
    )
