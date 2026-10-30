from elements import Stroke, draft_stroke, join_anchors, join_y, merge_drafts

from typekernel.project import glyph
from typekernel.system import System


@glyph("f", group="lc")
def f(system: System):
    asc = float(system.zones.asc)
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 28))
    jy = join_y(system)
    x = lsb + 50
    stem_pts = [
        system.map_xy(px, py)
        for px, py in [(x + 40, asc), (x, asc * 0.75), (x, jy)]
    ]
    bar_pts = [
        system.map_xy(px, py)
        for px, py in [(lsb + 10, xh * 0.7), (lsb + 130, xh * 0.7)]
    ]
    d_stem = draft_stroke(system, Stroke.through(stem_pts, tension=1.0), pressure=False)
    d_bar = draft_stroke(system, Stroke.through(bar_pts, tension=0.8), pressure=False)
    return merge_drafts(
        d_stem,
        d_bar,
        anchors=join_anchors(system, (x, jy), (lsb + 130, jy)),
        skeleton=d_stem.skeleton,
    )
