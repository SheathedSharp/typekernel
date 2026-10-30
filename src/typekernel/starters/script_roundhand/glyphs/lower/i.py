from elements import join_anchors, join_y, merge_drafts, stem

from typekernel.anatomy.pen import pen_dot
from typekernel.project import glyph
from typekernel.project.registry import GlyphDraft
from typekernel.system import System


@glyph("i", group="lc")
def i(system: System):
    xh = float(system.zones.x)
    body = stem(system, 140.0)
    d_dot = GlyphDraft(
        drawing=pen_dot(system, 140.0, xh + 90, radius=float(system.stem["lc"]) * 0.45)
    )
    jy = join_y(system)
    return merge_drafts(
        body,
        d_dot,
        anchors=join_anchors(system, (140.0, jy), (140.0, jy)),
        skeleton=body.skeleton,
    )
