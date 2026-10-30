from elements import Stroke, draft_stroke, join_anchors, join_y

from typekernel.project import glyph
from typekernel.system import System


@glyph("z", group="lc")
def z(system: System):
    """Z inset inside x-height so expand does not flip asc/desc extent flags."""
    xh = float(system.zones.x)
    w = float(system.tokens.get("n_width", 420)) * 0.9
    lsb = float(system.tokens.get("lsb_lc", 28))
    jy = join_y(system)
    st = float(system.stem["lc"])
    y_top = xh - st * 1.0
    y_bot = st * 1.0
    pts = [
        system.map_xy(x, y)
        for x, y in [
            (lsb, y_top),
            (lsb + w, y_top),
            (lsb, y_bot),
            (lsb + w, y_bot),
        ]
    ]
    return draft_stroke(
        system,
        Stroke.through(pts, tension=0.7),
        anchors=join_anchors(system, (lsb, jy), (lsb + w, jy)),
        pressure=False,
    )
