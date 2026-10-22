"""Punctuation and symbols derived from control ``n`` / ``o``.

Every glyph is drawn with :class:`~typekernel.geo.path_builder.PathBuilder` or
primitives (no boolean letter topology) so masters stay interpolatable.
"""

from __future__ import annotations

import math
from dataclasses import replace

from fontTools.misc.bezierTools import curveLineIntersections, splitCubicAtT

from typekernel.geo.contour import canonical_contour_start, reverse_contour, signed_area
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import ellipse_cubics
from typekernel.geo.point import Point
from typekernel.parts.compose import ComposedGlyph, GlyphAssembler
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    Cubic,
    NMetrics,
    OMetrics,
    n_metrics,
    o_metrics,
    c_yoke,
    _ccw,
    _curve,
    _cut,
    _n_record,
    _o_record,
    _pack,
    _quarters,
    c_from_o,
)
from typekernel.parts.diagonals import _hwidth
from typekernel.parts.figures import _outer_and_counters, _single_crossing
from typekernel.parts.primitives import bowl, horizontal_bar, stroke_polyline, tittle, vertical_stem
from typekernel.parts.slant_compensate import horizontal_slant_compensation
from typekernel.parts.transforms import mirror_x, scale, translate

__all__ = [
    "PUNCT_EXTENDED",
    "PUNCT_FORMS",
    "ampersand_from_n_o",
    "ampersand_yoke",
    "asterisk_from_n_o",
    "asterisk_yoke",
    "at_sign_from_n_o",
    "at_sign_yoke",
    "backslash_from_n_o",
    "backslash_yoke",
    "brace_left_from_n_o",
    "brace_left_yoke",
    "brace_right_from_n_o",
    "brace_right_yoke",
    "bracket_left_from_n_o",
    "bracket_left_yoke",
    "bracket_right_from_n_o",
    "bracket_right_yoke",
    "colon_from_n_o",
    "colon_yoke",
    "comma_from_n_o",
    "comma_yoke",
    "degree_from_n_o",
    "degree_yoke",
    "dollar_from_n_o",
    "dollar_yoke",
    "emdash_from_n_o",
    "emdash_yoke",
    "endash_from_n_o",
    "endash_yoke",
    "equal_from_n_o",
    "equal_yoke",
    "exclam_from_n_o",
    "exclam_yoke",
    "greater_from_n_o",
    "greater_yoke",
    "hash_from_n_o",
    "hash_yoke",
    "hyphen_from_n_o",
    "hyphen_yoke",
    "less_from_n_o",
    "less_yoke",
    "minus_from_n_o",
    "minus_yoke",
    "paren_left_from_n_o",
    "paren_left_yoke",
    "paren_right_from_n_o",
    "paren_right_yoke",
    "percent_from_n_o",
    "percent_yoke",
    "period_from_n_o",
    "period_yoke",
    "plus_from_n_o",
    "plus_yoke",
    "question_from_n_o",
    "question_yoke",
    "quote_ascii_from_n_o",
    "quote_ascii_yoke",
    "quote_dbl_ascii_from_n_o",
    "quote_dbl_ascii_yoke",
    "quote_double_left_from_n_o",
    "quote_double_left_yoke",
    "quote_double_right_from_n_o",
    "quote_double_right_yoke",
    "quote_single_left_from_n_o",
    "quote_single_left_yoke",
    "quote_single_right_from_n_o",
    "quote_single_right_yoke",
    "semicolon_from_n_o",
    "semicolon_yoke",
    "slash_from_n_o",
    "slash_yoke",
    "underscore_from_n_o",
    "underscore_yoke",
]

Pt = tuple[float, float]


def _ctx(n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None) -> DesignContext:
    return ctx or n.context or o.context


def _cw_hole(outline: Outline) -> Outline:
    """Hole contours are clockwise (negative signed area)."""
    return Outline(
        tuple(
            reverse_contour(c) if c.closed and signed_area(c) > 0 else c
            for c in outline.contours
        )
    )


def _pack_holes(
    ctx: DesignContext,
    record: object,
    *solids: Outline,
    holes: tuple[Outline, ...] = (),
    union: bool = False,
    subtract_holes: bool = False,
) -> ComposedGlyph:
    asm = GlyphAssembler(ctx).with_design(record)
    for outline in solids:
        asm.add(_ccw(outline))
    for hole in holes:
        asm.add_hole(_cw_hole(hole))
    if union:
        asm.union_solids()
    if subtract_holes:
        asm.subtract_holes()
    return asm.build()


def _pack_union(ctx: DesignContext, record: object, *solids: Outline) -> ComposedGlyph:
    return _pack_holes(ctx, record, *solids, union=True)


def _dot_size(n: NMetrics, ctx: DesignContext) -> float:
    """Cap size so heavy masters do not grow tittle into the x-height."""
    return min(n.stem * 0.95, n.x_height * 0.145)


def _dot_ellipse(cx: float, cy: float, size: float) -> Outline:
    """Four-cubic dot; stable under interpolation (unlike tiny rounded rects)."""
    b = PathBuilder()
    b.addEllipse(cx, cy + size / 2.0, size / 2.0, size / 2.0)
    return b.build()


def _plus_outline(cx: float, cy: float, arm: float, thickness: float) -> Outline:
    """Single-loop plus; no overlapping rectangles."""
    h = thickness / 2.0
    pts = [
        (cx - arm, cy + h),
        (cx - h, cy + h),
        (cx - h, cy + arm),
        (cx + h, cy + arm),
        (cx + h, cy + h),
        (cx + arm, cy + h),
        (cx + arm, cy - h),
        (cx + h, cy - h),
        (cx + h, cy - arm),
        (cx - h, cy - arm),
        (cx - h, cy - h),
        (cx - arm, cy - h),
    ]
    b = PathBuilder()
    b.moveTo(*pts[0])
    for p in pts[1:]:
        b.lineTo(*p)
    b.closePath()
    return _ccw(b.build())


def _dot_bottom_y(n: NMetrics) -> float:
    """Bottom of a baseline-area dot (period height)."""
    return n.x_height * 0.12


def _comma_tail(ctx: DesignContext, n: NMetrics, cx: float, dot_bottom: float, size: float) -> Outline:
    """Hook below the dot — fixed cubic topology."""
    b = PathBuilder()
    w = size * 0.42
    y0 = dot_bottom
    y1 = y0 - size * 0.35
    y2 = ctx.descender * 0.55
    x0 = cx + size * 0.08
    b.moveTo(x0 + w, y0)
    b.lineTo(x0 + w * 0.15, y1)
    b.curveTo(x0 - w * 0.35, y1 - size * 0.08, x0 - w * 0.55, y2 + size * 0.12, x0 - w * 0.45, y2)
    b.lineTo(x0 + w * 0.55, y2 + size * 0.18)
    b.curveTo(x0 + w * 0.85, y2 + size * 0.35, x0 + w * 1.05, y1 - size * 0.05, x0 + w, y0)
    b.closePath()
    return _ccw(b.build())


def _with_advance(g: ComposedGlyph, advance: float) -> ComposedGlyph:
    box = union_bounds(list(g.solids) + list(g.holes))
    ink = box[2] - box[0]
    moved = g.translated((advance - ink) / 2.0 - box[0])
    return replace(moved, advance=advance)


def _mirror_packed_solids(g: ComposedGlyph) -> ComposedGlyph:
    """Mirror solids about the glyph's ink center (after ``_with_advance``)."""
    box = union_bounds(list(g.solids) + list(g.holes))
    cx = (box[0] + box[2]) / 2.0
    solids = tuple(_ccw(mirror_x(s, at_x=cx)) for s in g.solids)
    return replace(g, solids=solids)


def _bar_y(n: NMetrics) -> float:
    return n.x_height * 0.52


def _hbar(
    ctx: DesignContext,
    x0: float,
    x1: float,
    y_center: float,
    *,
    thickness: float | None = None,
) -> Outline:
    t = ctx.thin if thickness is None else thickness
    return horizontal_bar(ctx, x0, x1, y_center - t / 2.0, thickness=t)



def period_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous period / full stop body — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    size = _dot_size(m, ctx)
    y = _dot_bottom_y(m)
    cx = m.width / 2.0
    return tittle(ctx, cx, y, size=size)


def comma_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> tuple[Outline, Outline]:
    """Continuous comma body (dot + tail) — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    size = _dot_size(m, ctx)
    y = _dot_bottom_y(m)
    cx = m.width / 2.0
    return tittle(ctx, cx, y, size=size), _comma_tail(ctx, m, cx, y, size)


def hyphen_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous hyphen / minus bar — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    w = m.counter * 0.55
    cx = m.width / 2.0
    return _hbar(ctx, cx - w / 2.0, cx + w / 2.0, _bar_y(m))


def minus_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous minus sign — Usage A (same bar as hyphen)."""
    return hyphen_yoke(ctx, n_metrics_rec=n_metrics_rec)


def quote_single_left_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous left single quote body — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    size = _dot_size(m, ctx) * 0.88
    y = m.x_height + m.stem * 0.35
    cx = m.width / 2.0
    return _comma_tail(ctx, m, cx, y, size)


def quote_single_right_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous right single / ASCII quote body — Usage A."""
    left = quote_single_left_yoke(ctx, n_metrics_rec=n_metrics_rec)
    box = union_bounds([left])
    cx = (box[0] + box[2]) / 2.0
    return _ccw(mirror_x(left, at_x=cx))


def quote_ascii_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous ASCII apostrophe body — Usage A."""
    return quote_single_right_yoke(ctx, n_metrics_rec=n_metrics_rec)


def quote_double_left_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> tuple[Outline, Outline]:
    """Continuous left double quote body — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    size = _dot_size(m, ctx) * 0.88
    y = m.x_height + m.stem * 0.35
    gap = size * 1.05
    cx = m.width / 2.0
    return (
        _comma_tail(ctx, m, cx - gap / 2.0, y, size),
        _comma_tail(ctx, m, cx + gap / 2.0, y, size),
    )


def quote_double_right_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> tuple[Outline, Outline]:
    """Continuous right double / ASCII double-quote body — Usage A."""
    left = quote_double_left_yoke(ctx, n_metrics_rec=n_metrics_rec)
    box = union_bounds(list(left))
    cx = (box[0] + box[2]) / 2.0
    return tuple(_ccw(mirror_x(part, at_x=cx)) for part in left)


def quote_dbl_ascii_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> tuple[Outline, Outline]:
    """Continuous ASCII double-quote body — Usage A."""
    return quote_double_right_yoke(ctx, n_metrics_rec=n_metrics_rec)


def period_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c)
    return _with_advance(_pack(c, m, {}, period_yoke(c, n_metrics_rec=m)), size * 1.65)


def comma_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _with_advance(
        _pack(c, m, {}, *comma_yoke(c, n_metrics_rec=m)), m.stem * 1.35
    )


def colon_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _with_advance(
        _pack(c, m, {}, *colon_yoke(c, n_metrics_rec=m)), m.stem * 1.15
    )


def semicolon_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _with_advance(
        _pack(c, m, {}, *semicolon_yoke(c, n_metrics_rec=m)), m.stem * 1.25
    )


def exclam_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, *exclam_yoke(c, n_metrics_rec=m))


def question_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    return _pack(c, m, {}, *question_yoke(c, n_metrics_rec=m, o_metrics_rec=om))


def hyphen_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    w = m.counter * 0.55
    return _with_advance(
        _pack(c, m, {}, hyphen_yoke(c, n_metrics_rec=m)), w + m.stem * 0.5
    )


def endash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    w = c.units_per_em * 0.5
    return _with_advance(
        _pack(c, m, {}, endash_yoke(c, n_metrics_rec=m)), w + m.stem * 0.35
    )


def emdash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    w = c.units_per_em
    return _with_advance(
        _pack(c, m, {}, emdash_yoke(c, n_metrics_rec=m)), w + m.stem * 0.25
    )


def minus_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    w = m.counter * 0.55
    return _with_advance(
        _pack(c, m, {}, minus_yoke(c, n_metrics_rec=m)), w + m.stem * 0.5
    )


def paren_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    return _pack(
        c, m, {}, paren_left_yoke(c, n_metrics_rec=m, o_metrics_rec=om)
    )


def paren_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    return _pack(
        c, m, {}, paren_right_yoke(c, n_metrics_rec=m, o_metrics_rec=om)
    )


def _bracket_outline(
    ctx: DesignContext, m: NMetrics, *, right: bool, curly: bool = False
) -> Outline:
    stem_w = m.stem * 0.88
    y_top = m.ascender * 0.94
    y_bot = ctx.descender * 0.72
    depth = m.counter * 0.38
    x0 = 0.0 if not right else m.width - depth - stem_w
    x1 = x0 + depth
    b = PathBuilder()
    if not curly:
        b.moveTo(x1, y_top)
        b.lineTo(x0, y_top)
        b.lineTo(x0, y_bot)
        b.lineTo(x1, y_bot)
        b.lineTo(x1, y_bot + ctx.thin)
        b.lineTo(x0 + stem_w, y_bot + ctx.thin)
        b.lineTo(x0 + stem_w, y_top - ctx.thin)
        b.lineTo(x1, y_top - ctx.thin)
        b.closePath()
        outline = _ccw(b.build())
        if right:
            outline = _ccw(mirror_x(outline, at_x=m.width / 2.0))
        return outline
    mid = (y_top + y_bot) / 2.0
    hook = depth * 0.55
    b.moveTo(x1, y_top)
    b.lineTo(x0 + stem_w * 0.35, y_top)
    b.curveTo(x0, y_top - hook * 0.2, x0, mid + hook, x0 + stem_w * 0.35, mid + hook * 0.35)
    b.curveTo(x0, mid - hook * 0.15, x0, y_bot + hook * 0.2, x0 + stem_w * 0.35, y_bot)
    b.lineTo(x1, y_bot)
    b.lineTo(x1, y_bot + ctx.thin)
    b.lineTo(x0 + stem_w, y_bot + ctx.thin)
    b.lineTo(x0 + stem_w, y_top - ctx.thin)
    b.lineTo(x1, y_top - ctx.thin)
    b.closePath()
    outline = _ccw(b.build())
    if right:
        outline = _ccw(mirror_x(outline, at_x=m.width / 2.0))
    return outline


def bracket_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, bracket_left_yoke(c, n_metrics_rec=m))


def bracket_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, bracket_right_yoke(c, n_metrics_rec=m))


def brace_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, brace_left_yoke(c, n_metrics_rec=m))


def brace_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, brace_right_yoke(c, n_metrics_rec=m))


def _diagonal_slash(
    c: DesignContext, m: NMetrics, *, back: bool = False
) -> Outline:
    h = m.ascender * 0.88
    w = m.width * 0.42
    cx = m.width / 2.0
    hw = _hwidth(m.stem, c.contrast, w / 2.0, h, weight=0.92)
    if back:
        pts = [(cx + w / 2.0, h), (cx - w / 2.0, 0.0)]
    else:
        pts = [(cx - w / 2.0, h), (cx + w / 2.0, 0.0)]
    return stroke_polyline(c, pts, width=hw * 2.0, join_radius=c.join_radius * 0.4)


def slash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, slash_yoke(c, n_metrics_rec=m))


def backslash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, backslash_yoke(c, n_metrics_rec=m))


def underscore_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _with_advance(
        _pack(c, m, {}, underscore_yoke(c, n_metrics_rec=m)), m.width
    )


def quote_single_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c) * 0.88
    return _with_advance(
        _pack(c, m, {}, quote_single_left_yoke(c, n_metrics_rec=m)), size * 1.25
    )


def quote_single_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c) * 0.88
    return _with_advance(
        _pack(c, m, {}, quote_single_right_yoke(c, n_metrics_rec=m)), size * 1.25
    )


def quote_ascii_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c) * 0.88
    return _with_advance(
        _pack(c, m, {}, quote_ascii_yoke(c, n_metrics_rec=m)), size * 1.25
    )


def quote_double_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c) * 0.88
    gap = size * 1.05
    return _with_advance(
        _pack(c, m, {}, *quote_double_left_yoke(c, n_metrics_rec=m)),
        gap + size * 1.1,
    )


def quote_double_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c) * 0.88
    gap = size * 1.05
    return _with_advance(
        _pack(c, m, {}, *quote_double_right_yoke(c, n_metrics_rec=m)),
        gap + size * 1.1,
    )


def quote_dbl_ascii_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c) * 0.88
    gap = size * 1.05
    return _with_advance(
        _pack(c, m, {}, *quote_dbl_ascii_yoke(c, n_metrics_rec=m)),
        gap + size * 1.1,
    )


def plus_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, plus_yoke(c, n_metrics_rec=m))


def equal_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, *equal_yoke(c, n_metrics_rec=m))


def less_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, less_yoke(c, n_metrics_rec=m))


def greater_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, greater_yoke(c, n_metrics_rec=m))


def asterisk_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, asterisk_yoke(c, n_metrics_rec=m))


def hash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, hash_yoke(c, n_metrics_rec=m))


def percent_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    solids, holes = percent_yoke(c, n_metrics_rec=m, o_metrics_rec=om)
    return _pack_holes(c, m, *solids, holes=holes)


def degree_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    outer, hole = degree_yoke(c, n_metrics_rec=m, o_metrics_rec=om)
    return _pack_holes(c, m, outer, holes=(hole,))


def _cubic_pts(q: tuple[Point, Point, Point, Point]) -> Cubic:
    pts = tuple((p.x, p.y) for p in q)
    return (pts[0], pts[1], pts[2], pts[3])


def _cubic4(b: Cubic) -> Cubic:
    return b


def _ampersand_lower_with_tail(
    c: DesignContext,
    m: NMetrics,
    *,
    cx: float,
    rx_l: float,
    cy_l: float,
    ry_l: float,
    thick_v: float,
    thick_h: float,
) -> tuple[Outline, Outline]:
    """Lower bowl with a Q-style tail splice (single outer contour, fixed topology)."""
    lcx = cx + rx_l * 0.30
    tv = thick_v * 0.94
    th = thick_h * 0.94
    q0, q1, q2, q3 = ellipse_cubics(lcx, cy_l, rx_l, ry_l)
    end = (cx - m.stem * 0.58, max(m.stem * 0.05, 3.0))
    k = math.cos(math.radians(45.0))
    start = (lcx - (rx_l - tv) * k, cy_l - (ry_l - th) * k)
    hw = _hwidth(m.stem, c.contrast, end[0] - start[0], end[1] - start[1], weight=0.65)
    hits: list[float] = []
    q2_pts = _cubic_pts(q2)
    for side in (-0.5, 0.5):
        a = (start[0] + side * hw, start[1])
        z = (end[0] + side * hw, end[1])
        far = (a[0] - (z[0] - a[0]), a[1] - (z[1] - a[1]))
        found = [
            i.t1
            for i in curveLineIntersections(list(q2_pts), [far, z])
            if 0.0 < i.t1 < 1.0
        ]
        if len(found) != 1:
            raise ValueError("ampersand tail does not meet the lower bowl once per edge")
        hits.append(found[0])
    t_lo, t_hi = sorted(hits)
    before, _, after = splitCubicAtT(*q2_pts, t_lo, t_hi)
    b = PathBuilder()
    b.moveTo(*_cubic_pts(q0)[0])
    _curve(b, _cubic_pts(q0))
    _curve(b, _cubic_pts(q1))
    _curve(b, _cubic4(before))
    b.lineTo(end[0] - hw / 2.0, end[1])
    b.lineTo(end[0] + hw / 2.0, end[1])
    b.lineTo(*after[0])
    _curve(b, _cubic4(after))
    _curve(b, _cubic_pts(q3))
    b.closePath()
    iq0, iq1, iq2, iq3 = ellipse_cubics(lcx, cy_l, rx_l - tv, ry_l - th)
    b.moveTo(iq0[0].x, iq0[0].y)
    for cubic in (iq0, iq1, iq2, iq3):
        _curve(b, _cubic_pts(cubic))
    b.closePath()
    outer, hole = b.build().contours
    return Outline((outer,)), Outline((reverse_contour(hole),))


def ampersand_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    """Single-storey ampersand: upper loop to cap, lower bowl, and tail."""
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    solids, holes = ampersand_yoke(c, n_metrics_rec=m, o_metrics_rec=om)
    return _pack_holes(c, m, *solids, holes=holes)


def at_sign_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    solids, holes = at_sign_yoke(c, n_metrics_rec=m, o_metrics_rec=om)
    return _pack_holes(c, m, *solids, holes=holes)


def _dollar_stacked_outline(
    c: DesignContext,
    m: NMetrics,
    om: OMetrics,
    *,
    waist: float = 0.50,
    top_scale: float = 0.90,
) -> Outline:
    """Stacked S-coupled rings (``8`` topology) with two counters — one solid, VF-safe.

    Baseline and ring-top stroke caps: fixed line detours (``xl``–``xr`` at
    ``y=0`` and at ``y_tab`` after splitting ``u0`` on a horizontal through the
    upper ring).
    """
    cap = m.x_height
    e = om.exponent
    cx = m.width / 2.0
    tv = min(om.thickness_h * 0.88, 0.24 * cap)
    ym = waist * cap
    rx_l = min(om.rx * 0.50, m.width * 0.23)
    rx_u = top_scale * rx_l
    ry_l = (ym + tv / 2.0) / 2.0
    ry_u = (cap - (ym - tv / 2.0)) / 2.0
    th = min(om.thickness_v * 0.88, 0.6 * rx_u)
    tv = min(tv, 0.6 * min(ry_u, ry_l))
    ry_l = (ym + tv / 2.0) / 2.0
    ry_u = (cap - (ym - tv / 2.0)) / 2.0
    cy_l, cy_u = ry_l, cap - ry_u
    y_tab = cy_u + ry_u * 0.995
    l0, l1, l2, l3 = _quarters(cx, cy_l, rx_l, ry_l, e)
    u0, u1, u2, u3 = _quarters(cx, cy_u, rx_u, ry_u, e)
    right = _single_crossing(l0, u3)
    left = _single_crossing(l1, u2)
    l0a, _ = splitCubicAtT(*l0, right.t1)
    _, u3b = splitCubicAtT(*u3, right.t2)
    u2a, _ = splitCubicAtT(*u2, left.t2)
    _, l1b = splitCubicAtT(*l1, left.t1)
    sw = min(m.stem * 0.72, tv * 1.05)
    xl, xr = cx - sw / 2.0, cx + sw / 2.0
    l2_lo, _ = _cut(l2, xl, horizontal=False)
    u0_lo, u0_hi = _cut(u0, y_tab, horizontal=True)
    b = PathBuilder()
    b.moveTo(xl, 0.0)
    b.lineTo(xr, 0.0)
    b.lineTo(*l3[0])
    _curve(b, l3)
    _curve(b, l0a)
    _curve(b, (l0a[3], u3b[1], u3b[2], u3b[3]))
    _curve(b, u0_lo)
    b.lineTo(xr, y_tab)
    b.lineTo(xl, y_tab)
    b.lineTo(*u0_hi[0])
    _curve(b, u0_hi)
    _curve(b, u1)
    _curve(b, u2a)
    _curve(b, (u2a[3], l1b[1], l1b[2], l1b[3]))
    _curve(b, l2_lo)
    b.lineTo(xl, 0.0)
    b.closePath()
    for qx, qy, rx, ry in (
        (cx, cy_l, rx_l - th, ry_l - tv),
        (cx, cy_u, rx_u - th, ry_u - tv),
    ):
        q = _quarters(qx, qy, rx, ry, e)
        b.moveTo(*q[0][0])
        for cubic in q:
            _curve(b, cubic)
        b.closePath()
    return _outer_and_counters(b.build())


def dollar_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    """Dollar: waist-coupled upper/lower rings (S spine) and two counters."""
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    return _pack_holes(c, m, dollar_yoke(c, n_metrics_rec=m, o_metrics_rec=om))



def colon_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> tuple[Outline, Outline]:
    """Continuous colon body — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    size = _dot_size(m, ctx)
    cx = m.width / 2.0
    gap = size * 1.35
    cy = m.x_height * 0.52
    top = tittle(ctx, cx, cy + gap / 2.0, size=size)
    bot = tittle(ctx, cx, cy - gap / 2.0 - size, size=size)
    return top, bot


def semicolon_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> tuple[Outline, Outline, Outline]:
    """Continuous semicolon body — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    size = _dot_size(m, ctx)
    cx = m.width / 2.0
    gap = size * 1.35
    cy = m.x_height * 0.52
    top = tittle(ctx, cx, cy + gap / 2.0, size=size)
    y = _dot_bottom_y(m)
    bot = tittle(ctx, cx, y, size=size)
    tail = _comma_tail(ctx, m, cx, y, size)
    return top, bot, tail


def exclam_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> tuple[Outline, Outline]:
    """Continuous exclamation body — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    size = _dot_size(m, ctx)
    cx = m.width / 2.0
    dot_y = _dot_bottom_y(m)
    gap = size * 0.45
    stem_bottom = dot_y + size + gap
    stem_w = m.stem * 0.92
    stem = vertical_stem(ctx, cx - stem_w / 2.0, stem_bottom, ctx.cap_height, width=stem_w)
    dot = tittle(ctx, cx, dot_y, size=size)
    return stem, dot


def question_yoke(
    ctx: DesignContext,
    *,
    n_metrics_rec: NMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
) -> tuple[Outline, Outline, Outline]:
    """Continuous question-mark body — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    om = o_metrics_rec or o_metrics(ctx)
    size = _dot_size(m, ctx)
    cx = m.width / 2.0
    dot_y = _dot_bottom_y(m)
    gap = size * 0.4
    stem_bottom = dot_y + size + gap
    stem_top = m.x_height * 0.36
    stem_w = m.stem * 0.9
    stem = vertical_stem(ctx, cx - stem_w / 2.0, stem_bottom, stem_top, width=stem_w)
    hook = scale(
        c_yoke(ctx, aperture=0.40, rx=om.rx, ry=om.ry),
        0.50,
        0.58,
        origin=(om.rx, om.x_height / 2.0),
    )
    hook = translate(hook, cx - om.rx * 0.50, m.x_height * 0.42)
    dot = tittle(ctx, cx, dot_y, size=size)
    return hook, stem, dot


def endash_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous en-dash bar — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    w = ctx.units_per_em * 0.5
    cx = m.width / 2.0
    return _hbar(ctx, cx - w / 2.0, cx + w / 2.0, _bar_y(m))


def emdash_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous em-dash bar — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    w = ctx.units_per_em
    cx = m.width / 2.0
    return _hbar(ctx, cx - w / 2.0, cx + w / 2.0, _bar_y(m))


def paren_left_yoke(
    ctx: DesignContext,
    *,
    n_metrics_rec: NMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
) -> Outline:
    """Continuous left parenthesis — Usage A."""
    return _paren_outline(ctx, n_metrics_rec, o_metrics_rec, right=False)


def paren_right_yoke(
    ctx: DesignContext,
    *,
    n_metrics_rec: NMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
) -> Outline:
    """Continuous right parenthesis — Usage A."""
    return _paren_outline(ctx, n_metrics_rec, o_metrics_rec, right=True)


def _paren_outline(
    ctx: DesignContext,
    n_metrics_rec: NMetrics | None,
    o_metrics_rec: OMetrics | None,
    *,
    right: bool,
) -> Outline:
    m = n_metrics_rec or n_metrics(ctx)
    om = o_metrics_rec or o_metrics(ctx)
    base = c_yoke(ctx, rx=om.rx, ry=om.ry)
    y_top = m.ascender * 0.96
    y_bot = ctx.descender * 0.72
    target_h = y_top - y_bot
    sy = target_h / om.x_height
    cy = om.x_height / 2.0
    shaped = scale(base, 1.0, sy, origin=(om.rx, cy))
    shaped = translate(shaped, 0.0, (y_top + y_bot) / 2.0 - cy)
    shaped = _ccw(shaped)
    if right:
        shaped = _ccw(mirror_x(shaped, at_x=om.rx))
    return shaped


def bracket_left_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous left bracket — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    return _bracket_outline(ctx, m, right=False)


def bracket_right_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous right bracket — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    return _bracket_outline(ctx, m, right=True)


def brace_left_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous left brace — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    return _bracket_outline(ctx, m, right=False, curly=True)


def brace_right_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous right brace — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    return _bracket_outline(ctx, m, right=True, curly=True)


def slash_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous solidus — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    return _diagonal_slash(ctx, m, back=False)


def backslash_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous reverse solidus — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    return _diagonal_slash(ctx, m, back=True)


def underscore_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous underscore — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    w = m.width
    y = ctx.descender * 0.82
    return _hbar(ctx, 0.0, w, y, thickness=ctx.thin * 0.85)


def plus_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous plus sign — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    cx = m.width / 2.0
    cy = _bar_y(m)
    arm = m.counter * 0.42
    th = min(m.stem, m.counter * 0.48)
    return _plus_outline(cx, cy, arm, th)


def equal_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> tuple[Outline, Outline]:
    """Continuous equals sign — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    cx = m.width / 2.0
    gap = m.stem * 0.85
    cy = _bar_y(m)
    w = m.counter * 0.55
    th = ctx.thin
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    lower = horizontal_bar(ctx, x0, x1, cy - gap / 2.0 - th, thickness=th)
    upper = horizontal_bar(ctx, x0, x1, cy + gap / 2.0, thickness=th)
    return lower, upper


def less_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous less-than — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    cx = m.width / 2.0
    cy = _bar_y(m)
    arm = m.counter * 0.38
    pts = [(cx + arm * 0.35, cy + arm), (cx - arm * 0.48, cy), (cx + arm * 0.35, cy - arm)]
    return stroke_polyline(ctx, pts, width=m.stem * 0.95, join_radius=ctx.join_radius * 0.35)


def greater_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous greater-than — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    cx = m.width / 2.0
    cy = _bar_y(m)
    arm = m.counter * 0.38
    pts = [(cx - arm * 0.35, cy + arm), (cx + arm * 0.48, cy), (cx - arm * 0.35, cy - arm)]
    return stroke_polyline(ctx, pts, width=m.stem * 0.95, join_radius=ctx.join_radius * 0.35)


def asterisk_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous asterisk — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    cx = m.width / 2.0
    cy = m.x_height * 0.58
    r_out = m.counter * 0.375
    r_in = r_out * 0.42
    pts: list[Pt] = []
    for k in range(6):
        a_out = math.radians(90.0 - k * 60.0)
        a_in = math.radians(90.0 - k * 60.0 - 30.0)
        pts.append((cx + r_out * math.cos(a_out), cy + r_out * math.sin(a_out)))
        pts.append((cx + r_in * math.cos(a_in), cy + r_in * math.sin(a_in)))
    b = PathBuilder()
    b.moveTo(*pts[0])
    for pt in pts[1:]:
        b.lineTo(*pt)
    b.closePath()
    return _ccw(b.build())


def hash_yoke(
    ctx: DesignContext, *, n_metrics_rec: NMetrics | None = None
) -> Outline:
    """Continuous number-sign body (unioned) — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    th = min(m.stem * 0.82, m.x_height * 0.11)
    inset = m.stem * 0.35
    x_l = m.width * 0.30
    x_r = m.width * 0.70 - th
    y_lo = m.x_height * 0.34
    y_hi = m.x_height * 0.66 - th
    v1 = vertical_stem(ctx, x_l, 0.0, m.x_height, width=th)
    v2 = vertical_stem(ctx, x_r, 0.0, m.x_height, width=th)
    th_h = th * horizontal_slant_compensation(ctx)
    h1 = horizontal_bar(ctx, inset, m.width - inset, y_lo, thickness=th_h)
    h2 = horizontal_bar(ctx, inset, m.width - inset, y_hi, thickness=th_h)
    glyph = _pack_union(ctx, m, v1, v2, h1, h2)
    solid = glyph.solids[0]
    return Outline(tuple(canonical_contour_start(ct) for ct in solid.contours))


def percent_yoke(
    ctx: DesignContext,
    *,
    n_metrics_rec: NMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
) -> tuple[tuple[Outline, Outline, Outline], tuple[Outline, Outline]]:
    """Continuous percent body (solids, holes) — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    om = o_metrics_rec or o_metrics(ctx)
    cx = m.width / 2.0
    ring = min(0.34, 0.20 + m.stem / max(m.x_height * 0.95, 1.0))
    ring_rx = max(om.rx * ring, m.stem * 0.62, m.x_height * 0.16)
    ring_ry = max(om.ry * ring, m.stem * 0.58, m.x_height * 0.15)
    thick_v = min(om.thickness_v * ring * 1.05, ring_rx * 0.42)
    thick_h = min(om.thickness_h * ring * 1.05, ring_ry * 0.42)
    y_top = m.x_height * 0.82
    y_bot = m.x_height * 0.18
    top_o, top_h = bowl(
        ctx, cx - om.rx * 0.52, y_top, rx=ring_rx, ry=ring_ry,
        thickness_v=thick_v, thickness_h=thick_h,
    )
    bot_o, bot_h = bowl(
        ctx, cx + om.rx * 0.52, y_bot, rx=ring_rx, ry=ring_ry,
        thickness_v=thick_v, thickness_h=thick_h,
    )
    hw = _hwidth(m.stem, ctx.contrast, m.width * 0.28, m.x_height * 0.5, weight=0.65)
    y_slash_top = y_top - ring_ry * 1.05
    y_slash_bot = y_bot + ring_ry * 1.05
    slash = stroke_polyline(
        ctx,
        [(cx - ring_rx * 0.85, y_slash_top), (cx + ring_rx * 0.85, y_slash_bot)],
        width=min(hw * 0.85, m.stem * 0.40, thick_v * 0.42, m.x_height * 0.016),
        join_radius=0.0,
    )
    return (top_o, bot_o, slash), (top_h, bot_h)


def degree_yoke(
    ctx: DesignContext,
    *,
    n_metrics_rec: NMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
) -> tuple[Outline, Outline]:
    """Continuous degree-sign body (outer, hole) — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    om = o_metrics_rec or o_metrics(ctx)
    cx = m.width / 2.0
    cy = m.x_height + om.ry * 0.28
    scale_f = 0.22
    outer, hole = bowl(
        ctx, cx, cy,
        rx=om.rx * scale_f, ry=om.ry * scale_f,
        thickness_v=om.thickness_v * scale_f, thickness_h=om.thickness_h * scale_f,
    )
    return outer, hole


def ampersand_yoke(
    ctx: DesignContext,
    *,
    n_metrics_rec: NMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
) -> tuple[tuple[Outline, Outline], tuple[Outline, Outline]]:
    """Continuous ampersand body (solids, holes) — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    om = o_metrics_rec or o_metrics(ctx)
    cx = m.width / 2.0
    rx_u = om.rx * 0.46
    cy_u = ctx.x_height + (ctx.cap_height - ctx.x_height) * 0.58
    ry_u = (ctx.cap_height - cy_u) + om.ry * 0.22
    wall_cap = 0.36
    thick_v = min(om.thickness_v * 0.9, rx_u * wall_cap, ry_u * wall_cap)
    thick_h = min(om.thickness_h * 0.9, ry_u * wall_cap, rx_u * wall_cap * 0.9)
    outer_u, hole_u = bowl(
        ctx, cx - rx_u * 0.28, cy_u, rx=rx_u, ry=ry_u,
        thickness_v=thick_v, thickness_h=thick_h,
    )
    rx_l = om.rx * 0.46
    cy_l = ctx.x_height * 0.36
    ry_l = om.ry * 0.48
    thick_l_v = min(om.thickness_v * 0.9, rx_l * wall_cap, ry_l * wall_cap)
    thick_l_h = min(om.thickness_h * 0.9, ry_l * wall_cap, rx_l * wall_cap * 0.9)
    outer_l, hole_l = _ampersand_lower_with_tail(
        ctx, m, cx=cx, rx_l=rx_l, cy_l=cy_l, ry_l=ry_l,
        thick_v=thick_l_v, thick_h=thick_l_h,
    )
    return (outer_u, outer_l), (hole_u, hole_l)


def at_sign_yoke(
    ctx: DesignContext,
    *,
    n_metrics_rec: NMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
) -> tuple[tuple[Outline, Outline], tuple[Outline, Outline]]:
    """Continuous at-sign body (solids, holes) — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    om = o_metrics_rec or o_metrics(ctx)
    cx = m.width / 2.0
    cy = m.x_height * 0.48
    scale_f = 0.92
    outer, ring_hole = bowl(
        ctx, cx, cy,
        rx=om.rx * scale_f, ry=om.ry * scale_f,
        thickness_v=om.thickness_v * scale_f, thickness_h=om.thickness_h * scale_f,
    )
    hole_r = om.rx * scale_f - om.thickness_v * scale_f
    heavy = max(0.0, (ctx.stem - 110.0) / 110.0)
    fill = hole_r / max(om.rx * scale_f, 1.0)
    belly_mul = 0.10 * min(1.0, fill / 0.49)
    belly_k = 0.34 + 0.008 * max(0.0, heavy - 0.76)
    dx = hole_r * 0.35
    belly_rx = hole_r * (belly_k - heavy * belly_mul)
    belly_ry = belly_rx * 0.85
    tv = min(om.thickness_v * scale_f * 0.65, belly_rx * 0.38)
    th = min(om.thickness_h * scale_f * 0.65, belly_ry * 0.38)
    inner_o, inner_h = bowl(
        ctx, cx + dx * 0.5, cy, rx=belly_rx, ry=belly_ry,
        thickness_v=tv, thickness_h=th,
    )
    return (outer, inner_o), (ring_hole, inner_h)


def dollar_yoke(
    ctx: DesignContext,
    *,
    n_metrics_rec: NMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
) -> Outline:
    """Continuous dollar body (stacked rings + counters) — Usage A."""
    m = n_metrics_rec or n_metrics(ctx)
    om = o_metrics_rec or o_metrics(ctx)
    return _dollar_stacked_outline(ctx, m, om)



PUNCT_FORMS = {
    ".": period_from_n_o,
    ",": comma_from_n_o,
    ":": colon_from_n_o,
    ";": semicolon_from_n_o,
    "!": exclam_from_n_o,
    "?": question_from_n_o,
    "-": hyphen_from_n_o,
    "\u2013": endash_from_n_o,
    "\u2014": emdash_from_n_o,
    "\u2212": minus_from_n_o,
    "(": paren_left_from_n_o,
    ")": paren_right_from_n_o,
    "[": bracket_left_from_n_o,
    "]": bracket_right_from_n_o,
    "{": brace_left_from_n_o,
    "}": brace_right_from_n_o,
    "/": slash_from_n_o,
    "\\": backslash_from_n_o,
    "_": underscore_from_n_o,
    "'": quote_ascii_from_n_o,
    '"': quote_dbl_ascii_from_n_o,
    "\u2018": quote_single_left_from_n_o,
    "\u2019": quote_single_right_from_n_o,
    "\u201c": quote_double_left_from_n_o,
    "\u201d": quote_double_right_from_n_o,
    "+": plus_from_n_o,
    "=": equal_from_n_o,
    "\u00b0": degree_from_n_o,
    "*": asterisk_from_n_o,
    "<": less_from_n_o,
    ">": greater_from_n_o,
    "#": hash_from_n_o,
    "&": ampersand_from_n_o,
    "%": percent_from_n_o,
    "@": at_sign_from_n_o,
    "$": dollar_from_n_o,
}

PUNCT_EXTENDED: dict[str, object] = {}
