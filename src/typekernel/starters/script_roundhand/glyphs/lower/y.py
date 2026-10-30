from elements import Stroke, draft_stroke, join_anchors, join_y

from typekernel.project import glyph
from typekernel.system import System


@glyph("y", group="lc")
def y(system: System):
    xh = float(system.zones.x)
    # Deep enough for descender extent flag, shallow enough for zone audit.
    desc = -180.0
    w = float(system.tokens.get("n_width", 420)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 28))
    jy = join_y(system)
    st = float(system.stem["lc"])
    pts = [
        system.map_xy(x, y)
        for x, y in [
            (lsb, xh - st * 0.3),
            (lsb + w * 0.45, st * 0.5),
            (lsb + w, xh - st * 0.3),
            (lsb + w * 0.55, desc * 0.45),
            (lsb + w * 0.4, desc),
        ]
    ]
    return draft_stroke(
        system,
        Stroke.through(pts, tension=1.0),
        anchors=join_anchors(system, (lsb, jy), (lsb + w, jy)),
        pressure=False,
    )
