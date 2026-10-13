"""Punctuation and symbols derived from control ``n`` / ``o``.

Every glyph is drawn with :class:`~typekernel.geo.path_builder.PathBuilder` or
primitives (no boolean letter topology) so masters stay interpolatable.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    NMetrics,
    OMetrics,
    _ccw,
    _curve,
    _n_record,
    _o_record,
    _pack,
    _quarters,
    _rev,
    c_from_o,
    e_from_o,
)
from typekernel.parts.diagonals import _hwidth
from typekernel.parts.primitives import horizontal_bar, stroke_polyline, tittle, vertical_stem
from typekernel.parts.transforms import mirror_x, scale, translate

__all__ = [
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


def _equal_outline(x0: float, x1: float, cy: float, gap: float, thickness: float) -> Outline:
    """Two stacked bars as one CCW loop."""
    t = thickness
    g = gap / 2.0
    y_top = cy + g + t
    y_mid_top = cy + g
    y_mid_bot = cy - g
    y_bot = cy - g - t
    b = PathBuilder()
    b.moveTo(x0, y_bot)
    b.lineTo(x1, y_bot)
    b.lineTo(x1, y_mid_bot)
    b.lineTo(x0, y_mid_bot)
    b.lineTo(x0, y_mid_top)
    b.lineTo(x1, y_mid_top)
    b.lineTo(x1, y_top)
    b.lineTo(x0, y_top)
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
    cx = m.stem / 2.0
    stem_h = m.x_height * 0.72
    stem = vertical_stem(c, 0.0, _dot_bottom_y(m) + size * 1.15, stem_h, width=m.stem * 0.92)
    dot = tittle(c, cx, stem_h + size * 0.55, size=size)
    return _pack(c, m, {}, stem, dot)


def question_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    size = _dot_size(m, c)
    cx = m.width / 2.0
    hook = scale(
        c_from_o(o, c, aperture=0.42).solids[0],
        0.52,
        0.62,
        origin=(om.rx, om.x_height / 2.0),
    )
    hook = translate(hook, cx - om.rx * 0.52, m.x_height * 0.18)
    dot = _dot_ellipse(cx, _dot_bottom_y(m), size)
    return _pack(c, m, {}, hook, dot)


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
    if right:
        shaped = mirror_x(shaped, at_x=om.rx)
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
        if right:
            return mirror_x(_ccw(b.build()), at_x=m.width / 2.0)
        return _ccw(b.build())
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
    if right:
        return mirror_x(_ccw(b.build()), at_x=m.width / 2.0)
    return _ccw(b.build())


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
    g = quote_single_left_from_n_o(n, o, ctx)
    m = _n_record(n)
    cx = m.width / 2.0
    solids = tuple(mirror_x(s, at_x=cx) for s in g.solids)
    return replace(g, solids=solids)


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
    g = quote_double_left_from_n_o(n, o, ctx)
    m = _n_record(n)
    cx = m.width / 2.0
    solids = tuple(mirror_x(s, at_x=cx) for s in g.solids)
    return replace(g, solids=solids)


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
    return _pack(
        c,
        m,
        {},
        _equal_outline(cx - w / 2.0, cx + w / 2.0, cy, gap, c.thin),
    )


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
    r = m.counter * 0.34
    t = m.stem * 0.78
    h = t / 2.0
    pts: list[Pt] = []
    for k in range(6):
        ang = math.radians(90.0 + k * 60.0)
        ux, uy = math.cos(ang), math.sin(ang)
        px, py = -uy, ux
        pts.extend(
            [
                (cx + px * h + ux * h, cy + py * h + uy * h),
                (cx + px * h + ux * r, cy + py * h + uy * r),
                (cx - px * h + ux * r, cy - py * h + uy * r),
                (cx - px * h + ux * h, cy - py * h + uy * h),
            ]
        )
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
    stem = m.stem * 0.82
    x_l = m.width * 0.28
    x_r = m.width * 0.72 - stem
    y_lo = m.x_height * 0.32
    y_hi = m.x_height * 0.68
    parts = [
        vertical_stem(c, x_l, 0.0, m.x_height, width=stem),
        vertical_stem(c, x_r, 0.0, m.x_height, width=stem),
        _hbar(c, x_l + stem, x_r, y_lo, thickness=stem),
        _hbar(c, x_l + stem, x_r, y_hi, thickness=stem),
    ]
    return _pack(c, m, {}, *parts)


def percent_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    size = om.thickness * 0.92
    cx = m.width / 2.0
    y_top = m.x_height * 0.78
    y_bot = m.x_height * 0.18
    left = _dot_ellipse(cx - om.rx * 0.48, y_top + size / 2.0, size)
    right = _dot_ellipse(cx + om.rx * 0.48, y_bot + size / 2.0, size)
    slash = _diagonal_slash(c, m, back=False)
    return _pack(c, m, {}, left, right, slash)


def _ring_outline_small(
    c: DesignContext, om: OMetrics, cx: float, cy: float, ring_scale: float
) -> Outline:
    rx = om.rx * ring_scale
    ry = om.ry * ring_scale
    thick = om.thickness * ring_scale
    q0, q1, q2, q3 = _quarters(cx, cy, rx, ry, om.exponent)
    i0, i1, i2, i3 = _quarters(cx, cy, rx - thick, ry - thick, om.exponent)
    b = PathBuilder()
    b.moveTo(*q0[0])
    for cubic in (q0, q1, q2, q3):
        _curve(b, cubic)
    b.lineTo(*i3[3])
    for cubic in (_rev(i3), _rev(i2), _rev(i1), _rev(i0)):
        _curve(b, cubic)
    b.closePath()
    return _ccw(b.build())


def degree_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    cx = m.width / 2.0
    cy = m.x_height + om.ry * 0.28
    ring = _ring_outline_small(c, om, cx, cy, 0.22)
    return _pack(c, m, {}, ring)


def ampersand_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    """Small ``e`` bowl plus a fixed diagonal leg (same topology at all stems)."""
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    e = e_from_o(o, c, aperture=c.aperture * 0.85)
    cx = m.width / 2.0
    hw = _hwidth(m.stem, c.contrast, m.counter * 0.35, m.x_height * 0.55, weight=0.88)
    leg = stroke_polyline(
        c,
        [
            (cx + m.counter * 0.32, m.x_height * 0.02),
            (cx - m.counter * 0.35, c.descender * 0.42),
        ],
        width=hw * 2.0,
        join_radius=c.join_radius * 0.35,
    )
    return _pack(c, m, {}, *e.solids, leg)


def at_sign_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    cx = m.width / 2.0
    cy = m.x_height * 0.48
    outer = _ring_outline_small(c, om, cx, cy, 0.95)
    inner = _ring_outline_small(c, om, cx + om.rx * 0.22, cy, 0.36)
    return _pack(c, m, {}, outer, inner)


def dollar_from_n_o(
    n: ComposedGlyph, o: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    c = _ctx(n, o, ctx)
    m = _n_record(n)
    om = _o_record(o)
    cx = m.width / 2.0
    top = _ring_outline_small(c, om, cx, m.x_height * 0.68, 0.32)
    bot = _ring_outline_small(c, om, cx, m.x_height * 0.32, 0.32)
    stem = vertical_stem(c, cx - m.stem / 2.0, c.descender * 0.4, m.ascender * 0.92, width=m.stem)
    return _pack(c, m, {}, stem, top, bot)


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
}

# Heavier symbols (overlap or variable topology at extreme stems) — build explicitly
# when needed: ``controls.build_all('#$%&@*<>' + '...')`` once recipes are tightened.
PUNCT_EXTENDED = {
    "*": asterisk_from_n_o,
    "<": less_from_n_o,
    ">": greater_from_n_o,
    "#": hash_from_n_o,
    "%": percent_from_n_o,
    "&": ampersand_from_n_o,
    "@": at_sign_from_n_o,
    "$": dollar_from_n_o,
}
