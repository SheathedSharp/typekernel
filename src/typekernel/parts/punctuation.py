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
    "asterisk_from_n_o",
    "at_sign_from_n_o",
    "backslash_from_n_o",
    "brace_left_from_n_o",
    "brace_right_from_n_o",
    "bracket_left_from_n_o",
    "bracket_right_from_n_o",
    "colon_from_n_o",
    "comma_from_n_o",
    "degree_from_n_o",
    "dollar_from_n_o",
    "emdash_from_n_o",
    "endash_from_n_o",
    "equal_from_n_o",
    "exclam_from_n_o",
    "greater_from_n_o",
    "hash_from_n_o",
    "hyphen_from_n_o",
    "less_from_n_o",
    "minus_from_n_o",
    "paren_left_from_n_o",
    "paren_right_from_n_o",
    "percent_from_n_o",
    "period_from_n_o",
    "plus_from_n_o",
    "question_from_n_o",
    "quote_ascii_from_n_o",
    "quote_dbl_ascii_from_n_o",
    "quote_double_left_from_n_o",
    "quote_double_right_from_n_o",
    "quote_single_left_from_n_o",
    "quote_single_right_from_n_o",
    "semicolon_from_n_o",
    "slash_from_n_o",
    "underscore_from_n_o",
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


def period_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c)
    y = _dot_bottom_y(m)
    cx = m.width / 2.0
    return _with_advance(_pack(c, m, {}, tittle(c, cx, y, size=size)), size * 1.65)


def comma_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c)
    y = _dot_bottom_y(m)
    cx = m.width / 2.0
    dot = tittle(c, cx, y, size=size)
    tail = _comma_tail(c, m, cx, y, size)
    return _with_advance(_pack(c, m, {}, dot, tail), m.stem * 1.35)


def colon_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c)
    cx = m.width / 2.0
    gap = size * 1.35
    cy = m.x_height * 0.52
    top = tittle(c, cx, cy + gap / 2.0, size=size)
    bot = tittle(c, cx, cy - gap / 2.0 - size, size=size)
    return _with_advance(_pack(c, m, {}, top, bot), m.stem * 1.15)


def semicolon_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c)
    cx = m.width / 2.0
    gap = size * 1.35
    cy = m.x_height * 0.52
    top = tittle(c, cx, cy + gap / 2.0, size=size)
    y = _dot_bottom_y(m)
    bot = tittle(c, cx, y, size=size)
    tail = _comma_tail(c, m, cx, y, size)
    return _with_advance(_pack(c, m, {}, top, bot, tail), m.stem * 1.25)


def exclam_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c)
    cx = m.width / 2.0
    dot_y = _dot_bottom_y(m)
    gap = size * 0.45
    stem_bottom = dot_y + size + gap
    stem_w = m.stem * 0.92
    stem = vertical_stem(
        c,
        cx - stem_w / 2.0,
        stem_bottom,
        c.cap_height,
        width=stem_w,
    )
    dot = tittle(c, cx, dot_y, size=size)
    return _pack(c, m, {}, stem, dot)


def question_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    size = _dot_size(m, c)
    cx = m.width / 2.0
    dot_y = _dot_bottom_y(m)
    gap = size * 0.4
    stem_bottom = dot_y + size + gap
    stem_top = m.x_height * 0.36
    stem_w = m.stem * 0.9
    stem = vertical_stem(c, cx - stem_w / 2.0, stem_bottom, stem_top, width=stem_w)
    hook = scale(
        c_from_o(o, c, aperture=0.40).solids[0],
        0.50,
        0.58,
        origin=(om.rx, om.x_height / 2.0),
    )
    hook = translate(hook, cx - om.rx * 0.50, m.x_height * 0.42)
    dot = tittle(c, cx, dot_y, size=size)
    return _pack(c, m, {}, hook, stem, dot)


def hyphen_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    w = m.counter * 0.55
    cx = m.width / 2.0
    bar = _hbar(c, cx - w / 2.0, cx + w / 2.0, _bar_y(m))
    return _with_advance(_pack(c, m, {}, bar), w + m.stem * 0.5)


def endash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    w = c.units_per_em * 0.5
    cx = m.width / 2.0
    bar = _hbar(c, cx - w / 2.0, cx + w / 2.0, _bar_y(m))
    return _with_advance(_pack(c, m, {}, bar), w + m.stem * 0.35)


def emdash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    w = c.units_per_em
    cx = m.width / 2.0
    bar = _hbar(c, cx - w / 2.0, cx + w / 2.0, _bar_y(m))
    return _with_advance(_pack(c, m, {}, bar), w + m.stem * 0.25)


def minus_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    return hyphen_from_n_o(n, o, ctx)


def _scaled_paren(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None, *, right: bool
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    base = c_from_o(o, c).solids[0]
    y_top = m.ascender * 0.96
    y_bot = c.descender * 0.72
    target_h = y_top - y_bot
    sy = target_h / om.x_height
    cy = om.x_height / 2.0
    shaped = scale(base, 1.0, sy, origin=(om.rx, cy))
    shaped = translate(shaped, 0.0, (y_top + y_bot) / 2.0 - cy)
    shaped = _ccw(shaped)
    if right:
        shaped = _ccw(mirror_x(shaped, at_x=om.rx))
    return _pack(c, m, {}, shaped)


def paren_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    return _scaled_paren(n, o, ctx, right=False)


def paren_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    return _scaled_paren(n, o, ctx, right=True)


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
    return _pack(c, m, {}, _bracket_outline(c, m, right=False))


def bracket_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, _bracket_outline(c, m, right=True))


def brace_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, _bracket_outline(c, m, right=False, curly=True))


def brace_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, _bracket_outline(c, m, right=True, curly=True))


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
    return _pack(c, m, {}, _diagonal_slash(c, m, back=False))


def backslash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    return _pack(c, m, {}, _diagonal_slash(c, m, back=True))


def underscore_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    w = m.width
    y = c.descender * 0.82
    bar = _hbar(c, 0.0, w, y, thickness=c.thin * 0.85)
    return _with_advance(_pack(c, m, {}, bar), w)


def quote_single_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c) * 0.88
    y = m.x_height + m.stem * 0.35
    cx = m.width / 2.0
    return _with_advance(_pack(c, m, {}, _comma_tail(c, m, cx, y, size)), size * 1.25)


def quote_single_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    return _mirror_packed_solids(quote_single_left_from_n_o(n, o, ctx))


def quote_ascii_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    return quote_single_right_from_n_o(n, o, ctx)


def quote_double_left_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    size = _dot_size(m, c) * 0.88
    y = m.x_height + m.stem * 0.35
    gap = size * 1.05
    cx = m.width / 2.0
    parts = [
        _comma_tail(c, m, cx - gap / 2.0, y, size),
        _comma_tail(c, m, cx + gap / 2.0, y, size),
    ]
    return _with_advance(_pack(c, m, {}, *parts), gap + size * 1.1)


def quote_double_right_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    return _mirror_packed_solids(quote_double_left_from_n_o(n, o, ctx))


def quote_dbl_ascii_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    return quote_double_right_from_n_o(n, o, ctx)


def plus_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    cx = m.width / 2.0
    cy = _bar_y(m)
    arm = m.counter * 0.42
    t = min(m.stem, m.counter * 0.48)
    return _pack(c, m, {}, _plus_outline(cx, cy, arm, t))


def equal_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    cx = m.width / 2.0
    gap = m.stem * 0.85
    cy = _bar_y(m)
    w = m.counter * 0.55
    t = c.thin
    x0, x1 = cx - w / 2.0, cx + w / 2.0
    lower = horizontal_bar(c, x0, x1, cy - gap / 2.0 - t, thickness=t)
    upper = horizontal_bar(c, x0, x1, cy + gap / 2.0, thickness=t)
    return _pack(c, m, {}, lower, upper)


def less_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    cx = m.width / 2.0
    cy = _bar_y(m)
    arm = m.counter * 0.38
    pts = [(cx + arm * 0.35, cy + arm), (cx - arm * 0.48, cy), (cx + arm * 0.35, cy - arm)]
    return _pack(c, m, {}, stroke_polyline(c, pts, width=m.stem * 0.95, join_radius=c.join_radius * 0.35))


def greater_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    cx = m.width / 2.0
    cy = _bar_y(m)
    arm = m.counter * 0.38
    pts = [(cx - arm * 0.35, cy + arm), (cx + arm * 0.48, cy), (cx - arm * 0.35, cy - arm)]
    return _pack(c, m, {}, stroke_polyline(c, pts, width=m.stem * 0.95, join_radius=c.join_radius * 0.35))


def asterisk_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    cx = m.width / 2.0
    cy = m.x_height * 0.58
    r_out = m.counter * 0.34
    r_in = r_out * 0.42
    pts: list[Pt] = []
    for k in range(6):
        a_out = math.radians(90.0 - k * 60.0)
        a_in = math.radians(90.0 - k * 60.0 - 30.0)
        pts.append((cx + r_out * math.cos(a_out), cy + r_out * math.sin(a_out)))
        pts.append((cx + r_in * math.cos(a_in), cy + r_in * math.sin(a_in)))
    b = PathBuilder()
    b.moveTo(*pts[0])
    for p in pts[1:]:
        b.lineTo(*p)
    b.closePath()
    return _pack(c, m, {}, _ccw(b.build()))


def hash_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    t = min(m.stem * 0.82, m.x_height * 0.11)
    inset = m.stem * 0.35
    x_l = m.width * 0.30
    x_r = m.width * 0.70 - t
    y_lo = m.x_height * 0.34
    y_hi = m.x_height * 0.66 - t
    v1 = vertical_stem(c, x_l, 0.0, m.x_height, width=t)
    v2 = vertical_stem(c, x_r, 0.0, m.x_height, width=t)
    th = t * horizontal_slant_compensation(c)
    h1 = horizontal_bar(c, inset, m.width - inset, y_lo, thickness=th)
    h2 = horizontal_bar(c, inset, m.width - inset, y_hi, thickness=th)
    glyph = _pack_union(c, m, v1, v2, h1, h2)
    solid = glyph.solids[0]
    normed = Outline(tuple(canonical_contour_start(ct) for ct in solid.contours))
    return replace(glyph, solids=(normed,))


def percent_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    cx = m.width / 2.0
    ring = min(0.34, 0.20 + m.stem / max(m.x_height * 0.95, 1.0))
    ring_rx = max(om.rx * ring, m.stem * 0.62, m.x_height * 0.16)
    ring_ry = max(om.ry * ring, m.stem * 0.58, m.x_height * 0.15)
    thick_v = min(om.thickness_v * ring * 1.05, ring_rx * 0.42)
    thick_h = min(om.thickness_h * ring * 1.05, ring_ry * 0.42)
    y_top = m.x_height * 0.82
    y_bot = m.x_height * 0.18
    top_o, top_h = bowl(
        c,
        cx - om.rx * 0.52,
        y_top,
        rx=ring_rx,
        ry=ring_ry,
        thickness_v=thick_v,
        thickness_h=thick_h,
    )
    bot_o, bot_h = bowl(
        c,
        cx + om.rx * 0.52,
        y_bot,
        rx=ring_rx,
        ry=ring_ry,
        thickness_v=thick_v,
        thickness_h=thick_h,
    )
    hw = _hwidth(m.stem, c.contrast, m.width * 0.28, m.x_height * 0.5, weight=0.65)
    y_slash_top = y_top - ring_ry * 1.05
    y_slash_bot = y_bot + ring_ry * 1.05
    slash = stroke_polyline(
        c,
        [
            (cx - ring_rx * 0.85, y_slash_top),
            (cx + ring_rx * 0.85, y_slash_bot),
        ],
        width=min(hw * 0.85, m.stem * 0.40, thick_v * 0.42, m.x_height * 0.016),
        join_radius=0.0,
    )
    return _pack_holes(c, m, top_o, bot_o, slash, holes=(top_h, bot_h))


def degree_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    cx = m.width / 2.0
    cy = m.x_height + om.ry * 0.28
    scale = 0.22
    outer, hole = bowl(
        c,
        cx,
        cy,
        rx=om.rx * scale,
        ry=om.ry * scale,
        thickness_v=om.thickness_v * scale,
        thickness_h=om.thickness_h * scale,
    )
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
    cx = m.width / 2.0
    thick_v = om.thickness_v * 0.9
    thick_h = om.thickness_h * 0.9
    rx_u = om.rx * 0.46
    cy_u = c.x_height + (c.cap_height - c.x_height) * 0.58
    ry_u = (c.cap_height - cy_u) + om.ry * 0.22
    outer_u, hole_u = bowl(
        c, cx - rx_u * 0.28, cy_u, rx=rx_u, ry=ry_u, thickness_v=thick_v, thickness_h=thick_h
    )
    rx_l = om.rx * 0.46
    cy_l = c.x_height * 0.36
    ry_l = om.ry * 0.48
    outer_l, hole_l = _ampersand_lower_with_tail(
        c,
        m,
        cx=cx,
        rx_l=rx_l,
        cy_l=cy_l,
        ry_l=ry_l,
        thick_v=thick_v,
        thick_h=thick_h,
    )
    return _pack_holes(c, m, outer_u, outer_l, holes=(hole_u, hole_l))


def at_sign_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    cx = m.width / 2.0
    cy = m.x_height * 0.48
    scale = 0.92
    outer, ring_hole = bowl(
        c,
        cx,
        cy,
        rx=om.rx * scale,
        ry=om.ry * scale,
        thickness_v=om.thickness_v * scale,
        thickness_h=om.thickness_h * scale,
    )
    hole_r = om.rx * scale - om.thickness_v * scale
    heavy = max(0.0, (c.stem - 110.0) / 110.0)
    dx = hole_r * 0.35
    belly_rx = hole_r * (0.34 - heavy * 0.10)
    belly_ry = belly_rx * 0.85
    belly_cy = cy
    tv = min(om.thickness_v * scale * 0.65, belly_rx * 0.38)
    th = min(om.thickness_h * scale * 0.65, belly_ry * 0.38)
    inner_o, inner_h = bowl(
        c,
        cx + dx * 0.5,
        belly_cy,
        rx=belly_rx,
        ry=belly_ry,
        thickness_v=tv,
        thickness_h=th,
    )
    return _pack_holes(c, m, outer, inner_o, holes=(ring_hole, inner_h))


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
    outline = _dollar_stacked_outline(c, m, om)
    return _pack_holes(c, m, outline)


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
