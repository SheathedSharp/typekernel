from elements import Stroke, draft_stroke, join_anchors, join_y, merge_drafts

from typekernel.anatomy.pen import pen_dot
from typekernel.project import glyph
from typekernel.project.registry import GlyphDraft
from typekernel.system import System


@glyph("j", group="lc")
def j(system: System):
    xh = float(system.zones.x)
    desc = -180.0
    lsb = float(system.tokens.get("lsb_lc", 28))
    jy = join_y(system)
    x = lsb + 80
    # Stem only to x-height (dot supplies asc/dot); hook into desc band.
    pts = [
        system.map_xy(px, py)
        for px, py in [(x, xh), (x, 0.0), (x - 18, desc * 0.45), (x - 40, desc)]
    ]
    body = draft_stroke(system, Stroke.through(pts, tension=0.95), pressure=False)
    d_dot = GlyphDraft(
        drawing=pen_dot(system, x, xh + 70, radius=float(system.stem["lc"]) * 0.4)
    )
    return merge_drafts(
        body,
        d_dot,
        anchors=join_anchors(system, (x, jy), (x, jy)),
        skeleton=body.skeleton,
    )
