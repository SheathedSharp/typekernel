"""Cap-height (.case) variants of above marks — slightly larger geometry."""

from __future__ import annotations

from typekernel.anatomy import bowl, crossbar, diagonal_pair, dot, drop
from typekernel.draw import Writer
from typekernel.project import GlyphDraft, glyph
from typekernel.system import System


def _st(system: System) -> float:
    # Case marks track the UC stem a bit more closely.
    return float(system.stem.get("uc", system.stem["lc"])) * 0.5


@glyph("acutecomb.case", unicodes=(), group="marks.case", traits=("mark",))
def acutecomb_case(system: System):
    st = _st(system)
    h = st * 2.4
    body = drop((st * 0.6, h), (0.0, st * 0.15), width=st * 0.9, name="drop")
    return GlyphDraft(drawing=body, anchors={"_top": (0.0, 0.0)})


@glyph("gravecomb.case", unicodes=(), group="marks.case", traits=("mark",))
def gravecomb_case(system: System):
    st = _st(system)
    h = st * 2.4
    body = drop((-st * 0.6, h), (0.0, st * 0.15), width=st * 0.9, name="drop")
    return GlyphDraft(drawing=body, anchors={"_top": (0.0, 0.0)})


@glyph("circumflexcomb.case", unicodes=(), group="marks.case", traits=("mark",))
def circumflexcomb_case(system: System):
    st = _st(system)
    w = st * 2.8
    h = st * 1.85
    d = diagonal_pair((0.0, h), (-w / 2, st * 0.15), (w / 2, st * 0.15), weight=st, name="diag")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("caroncomb.case", unicodes=(), group="marks.case", traits=("mark",))
def caroncomb_case(system: System):
    st = _st(system)
    w = st * 2.8
    h = st * 1.85
    d = diagonal_pair((0.0, st * 0.15), (-w / 2, h), (w / 2, h), weight=st, name="diag")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("dieresiscomb.case", unicodes=(), group="marks.case", traits=("mark",))
def dieresiscomb_case(system: System):
    st = _st(system) * 1.15
    diam = st * 0.9
    gap = st * 0.6
    y = diam / 2 + st * 0.3
    d = dot((-gap, y), diam, name="dot.l") + dot((gap, y), diam, name="dot.r")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("ringcomb.case", unicodes=(), group="marks.case", traits=("mark",))
def ringcomb_case(system: System):
    st = _st(system) * 0.95
    r = st * 1.45
    cy = r + st * 0.4
    d = bowl((0.0, cy), r, r, thick=st, thin=st * 0.9, name="bowl")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("tildecomb.case", unicodes=(), group="marks.case", traits=("mark",))
def tildecomb_case(system: System):
    st = _st(system) * 0.95
    w = st * 3.4
    y = st * 1.0
    amp = st * 0.6
    drawing = (
        Writer()
        .start((-w / 2, y))
        .corner("bar.l")
        .curve((-w / 4, y + amp), (w / 4, y - amp), (w / 2, y))
        .corner("bar.r")
        .line((w / 2, y - st))
        .corner("bar.r.b")
        .curve((w / 4, y - amp - st), (-w / 4, y + amp - st), (-w / 2, y - st))
        .corner("bar.l.b")
        .line((-w / 2, y))
        .close()
        .build()
    )
    return GlyphDraft(drawing=drawing, anchors={"_top": (0.0, 0.0)})


@glyph("macroncomb.case", unicodes=(), group="marks.case", traits=("mark",))
def macroncomb_case(system: System):
    st = _st(system) * 0.85
    w = st * 3.2
    y = st * 0.75
    d = crossbar(-w / 2, w / 2, y, thick=st, name="bar", ends="none")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("brevecomb.case", unicodes=(), group="marks.case", traits=("mark",))
def brevecomb_case(system: System):
    st = _st(system) * 0.95
    w = st * 3.0
    y_top = st * 1.45
    y_bot = st * 0.25
    drawing = (
        Writer()
        .start((-w / 2, y_top))
        .corner("arch.l")
        .curve((-w / 2, y_bot), (w / 2, y_bot), (w / 2, y_top))
        .corner("arch.r")
        .line((w / 2, y_top - st))
        .corner("arch.r.i")
        .curve((w / 2, y_bot + st), (-w / 2, y_bot + st), (-w / 2, y_top - st))
        .corner("arch.l.i")
        .line((-w / 2, y_top))
        .close()
        .build()
    )
    return GlyphDraft(drawing=drawing, anchors={"_top": (0.0, 0.0)})


@glyph("dotaccentcomb.case", unicodes=(), group="marks.case", traits=("mark",))
def dotaccentcomb_case(system: System):
    st = _st(system) * 1.1
    diam = st * 1.0
    d = dot((0.0, diam / 2 + st * 0.25), diam, name="dot")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("cedillacomb.case", unicodes=(), group="marks.case", traits=("mark",))
def cedillacomb_case(system: System):
    st = _st(system)
    body = drop((0.0, -st * 0.1), (0.0, -st * 2.6), width=st * 1.15, name="drop")
    return GlyphDraft(drawing=body, anchors={"_bottom": (0.0, 0.0)})


@glyph("ogonekcomb.case", unicodes=(), group="marks.case", traits=("mark",))
def ogonekcomb_case(system: System):
    from typekernel.anatomy import hook

    st = _st(system)
    body = hook(
        0.0,
        0.0,
        (st * 1.7, -st * 2.2),
        thick=st,
        thin=st * 0.75,
        depth=st * 1.3,
        name="hook",
    )
    return GlyphDraft(drawing=body, anchors={"_ogonek": (0.0, 0.0), "_bottom": (0.0, 0.0)})
