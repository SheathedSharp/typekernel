"""Combining marks (zero width, mark anchors) for composite accented glyphs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.control import _ccw, _n_record, _pack, n_metrics

__all__ = [
    "MARK_BUILDERS",
    "acute_comb",
    "cedilla_comb",
    "circumflex_comb",
    "dieresis_comb",
    "dotaccent_comb",
    "grave_comb",
    "macron_comb",
    "ring_comb",
    "tilde_comb",
]


def _pack_mark(
    ctx: DesignContext,
    outline: Outline,
    anchors: dict[str, tuple[float, float]],
) -> ComposedGlyph:
    m = n_metrics(ctx)
    g = _pack(ctx, m, anchors, outline)
    return replace(g, advance=0.0)


def acute_comb(n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    w = m.stem * 0.82
    h = m.stem * 1.05
    y = m.x_height
    b = PathBuilder()
    b.moveTo(-w / 2.0, y + h * 0.12)
    b.lineTo(w / 2.0, y + h * 0.12)
    b.lineTo(0.0, y + h)
    b.closePath()
    return _pack_mark(c, _ccw(b.build()), {"_top": (0.0, y)})


def grave_comb(n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    w = m.stem * 0.82
    h = m.stem * 1.05
    y = m.x_height
    b = PathBuilder()
    b.moveTo(-w / 2.0, y + h)
    b.lineTo(w / 2.0, y + h)
    b.lineTo(0.0, y + h * 0.12)
    b.closePath()
    return _pack_mark(c, _ccw(b.build()), {"_top": (0.0, y)})


def circumflex_comb(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    w = m.counter * 0.28
    h = m.stem * 1.1
    y = m.x_height
    b = PathBuilder()
    b.moveTo(-w, y + h * 0.15)
    b.lineTo(0.0, y + h)
    b.lineTo(w, y + h * 0.15)
    b.lineTo(w - m.stem * 0.35, y + h * 0.15)
    b.lineTo(0.0, y + h * 0.55)
    b.lineTo(-w + m.stem * 0.35, y + h * 0.15)
    b.closePath()
    return _pack_mark(c, _ccw(b.build()), {"_top": (0.0, y)})


def dieresis_comb(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    s = min(m.stem * 0.55, m.x_height * 0.09)
    gap = s * 1.15
    y = m.x_height + s * 1.35
    bl = PathBuilder()
    bl.addEllipse(-gap / 2.0, y, s / 2.0, s / 2.0)
    left = bl.build()
    br = PathBuilder()
    br.addEllipse(gap / 2.0, y, s / 2.0, s / 2.0)
    right = br.build()
    g = _pack(c, m, {"_top": (0.0, m.x_height)}, left, right)
    return replace(g, advance=0.0)


def dotaccent_comb(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    s = min(m.stem * 0.55, m.x_height * 0.09)
    y = m.x_height + s * 1.35
    bd = PathBuilder()
    bd.addEllipse(0.0, y, s / 2.0, s / 2.0)
    dot = bd.build()
    return _pack_mark(c, dot, {"_top": (0.0, m.x_height)})


def tilde_comb(n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    w = m.counter * 0.32
    y0 = m.x_height + m.stem * 0.55
    t = m.stem * 0.38
    b = PathBuilder()
    b.moveTo(-w, y0)
    b.curveTo(-w * 0.35, y0 + t, w * 0.35, y0 - t * 0.35, w, y0)
    b.lineTo(w, y0 + t * 0.55)
    b.curveTo(w * 0.35, y0 + t * 0.55, -w * 0.35, y0 + t * 0.2, -w, y0 + t * 0.55)
    b.closePath()
    return _pack_mark(c, _ccw(b.build()), {"_top": (0.0, m.x_height)})


def macron_comb(n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    w = m.counter * 0.42
    t = m.stem * 0.38
    y = m.x_height + m.stem * 0.65
    b = PathBuilder()
    b.moveTo(-w / 2.0, y)
    b.lineTo(w / 2.0, y)
    b.lineTo(w / 2.0, y + t)
    b.lineTo(-w / 2.0, y + t)
    b.closePath()
    return _pack_mark(c, _ccw(b.build()), {"_top": (0.0, m.x_height)})


def ring_comb(n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    r = m.stem * 0.42
    y = m.x_height + r * 1.65
    inner = m.stem * 0.22
    bo = PathBuilder()
    bo.addEllipse(0.0, y, r, r * 0.92)
    outer = bo.build()
    bh = PathBuilder()
    bh.addEllipse(0.0, y, max(r - inner, 1.0), max((r - inner) * 0.92, 1.0))
    hole = bh.build()
    g = (
        GlyphAssembler(c)
        .with_design(m)
        .add(outer)
        .add_hole(hole)
        .subtract_holes()
        .anchor("_top", 0.0, m.x_height)
        .build()
    )
    return replace(g, advance=0.0)


def cedilla_comb(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = ctx or n.context
    m = _n_record(n)
    w = m.stem * 0.55
    b = PathBuilder()
    b.moveTo(w * 0.35, 0.0)
    b.lineTo(-w * 0.15, 0.0)
    b.curveTo(-w * 0.55, c.descender * 0.15, -w * 0.35, c.descender * 0.42, w * 0.05, c.descender * 0.38)
    b.lineTo(w * 0.45, c.descender * 0.28)
    b.curveTo(w * 0.65, c.descender * 0.08, w * 0.55, 0.0, w * 0.35, 0.0)
    b.closePath()
    return _pack_mark(c, _ccw(b.build()), {"_bottom": (0.0, 0.0)})


MarkBuilder = Callable[[ComposedGlyph, ComposedGlyph, DesignContext | None], ComposedGlyph]

MARK_BUILDERS: dict[str, MarkBuilder] = {
    "acutecomb": acute_comb,
    "gravecomb": grave_comb,
    "circumflexcomb": circumflex_comb,
    "dieresiscomb": dieresis_comb,
    "dotaccentcomb": dotaccent_comb,
    "tildecomb": tilde_comb,
    "macroncomb": macron_comb,
    "ringcomb": ring_comb,
    "cedillacomb": cedilla_comb,
}

def _case_mark(
    builder: MarkBuilder, n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None
) -> ComposedGlyph:
    """Cap-height variant: flatter mark sitting on ``cap_height``."""
    c = ctx or n.context
    m = _n_record(n)
    cap_n = replace(m, x_height=c.cap_height, ascender=c.ascender)
    from typekernel.parts.control import build_n

    cap_glyph = build_n(c, cap_n)
    return builder(cap_glyph, o, c)


CASE_MARK_BUILDERS: dict[str, MarkBuilder] = {
    f"{name}.case": (lambda n, o, c, fn=fn: _case_mark(fn, n, o, c))  # type: ignore[misc]
    for name, fn in MARK_BUILDERS.items()
    if name != "cedillacomb"
}


MARK_UNICODE: dict[str, int] = {
    "acutecomb": 0x0301,
    "gravecomb": 0x0300,
    "circumflexcomb": 0x0302,
    "dieresiscomb": 0x0308,
    "dotaccentcomb": 0x0307,
    "tildecomb": 0x0303,
    "macroncomb": 0x0304,
    "ringcomb": 0x030A,
    "cedillacomb": 0x0327,
}
