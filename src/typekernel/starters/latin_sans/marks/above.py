"""Combining above marks for latin-sans — anatomy dots / drops / bowls."""

from __future__ import annotations

from typekernel.anatomy import bowl, crossbar, diagonal_pair, dot, drop
from typekernel.draw import Writer
from typekernel.project import GlyphDraft, glyph
from typekernel.system import System


def _st(system: System) -> float:
    return float(system.stem["lc"])


@glyph("acutecomb", unicodes=(0x0301,), group="marks", traits=("mark",))
def acutecomb(system: System):
    st = _st(system) * 0.55
    h = st * 2.2
    body = drop((st * 0.55, h), (0.0, st * 0.15), width=st * 0.85, name="drop")
    return GlyphDraft(drawing=body, anchors={"_top": (0.0, 0.0)})


@glyph("gravecomb", unicodes=(0x0300,), group="marks", traits=("mark",))
def gravecomb(system: System):
    st = _st(system) * 0.55
    h = st * 2.2
    body = drop((-st * 0.55, h), (0.0, st * 0.15), width=st * 0.85, name="drop")
    return GlyphDraft(drawing=body, anchors={"_top": (0.0, 0.0)})


@glyph("circumflexcomb", unicodes=(0x0302,), group="marks", traits=("mark",))
def circumflexcomb(system: System):
    st = _st(system) * 0.5
    w = st * 2.6
    h = st * 1.7
    d = diagonal_pair(
        (0.0, h),
        (-w / 2, st * 0.15),
        (w / 2, st * 0.15),
        weight=st,
        name="diag",
    )
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("caroncomb", unicodes=(0x030C,), group="marks", traits=("mark",))
def caroncomb(system: System):
    st = _st(system) * 0.5
    w = st * 2.6
    h = st * 1.7
    # Inverted V: apex at bottom near attachment, feet high.
    d = diagonal_pair(
        (0.0, st * 0.15),
        (-w / 2, h),
        (w / 2, h),
        weight=st,
        name="diag",
    )
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("dieresiscomb", unicodes=(0x0308,), group="marks", traits=("mark",))
def dieresiscomb(system: System):
    st = _st(system)
    diam = st * 0.85
    gap = st * 0.55
    y = diam / 2 + st * 0.25
    d = dot((-gap, y), diam, name="dot.l") + dot((gap, y), diam, name="dot.r")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("ringcomb", unicodes=(0x030A,), group="marks", traits=("mark",))
def ringcomb(system: System):
    st = _st(system) * 0.45
    r = st * 1.35
    cy = r + st * 0.35
    d = bowl((0.0, cy), r, r, thick=st, thin=st * 0.9, name="bowl")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("tildecomb", unicodes=(0x0303,), group="marks", traits=("mark",))
def tildecomb(system: System):
    st = _st(system) * 0.45
    w = st * 3.2
    y = st * 0.9
    amp = st * 0.55
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


@glyph("macroncomb", unicodes=(0x0304,), group="marks", traits=("mark",))
def macroncomb(system: System):
    st = _st(system) * 0.4
    w = st * 3.0
    y = st * 0.7
    d = crossbar(-w / 2, w / 2, y, thick=st, name="bar", ends="none")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})


@glyph("brevecomb", unicodes=(0x0306,), group="marks", traits=("mark",))
def brevecomb(system: System):
    st = _st(system) * 0.45
    w = st * 2.8
    y_top = st * 1.35
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


@glyph("dotaccentcomb", unicodes=(0x0307,), group="marks", traits=("mark",))
def dotaccentcomb(system: System):
    st = _st(system)
    diam = st * 0.95
    d = dot((0.0, diam / 2 + st * 0.2), diam, name="dot")
    return GlyphDraft(drawing=d, anchors={"_top": (0.0, 0.0)})
