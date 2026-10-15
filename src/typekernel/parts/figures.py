"""Lining figures — drawn from the cap ``H`` and ``O`` records.

Figures stand at cap height with strokes a little lighter than the cap stem
(they sit between lowercase and capitals in colour) and a common width, so
:func:`tabular` can give them one advance for columns of numbers.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import Any

from fontTools.misc.bezierTools import (
    curveCurveIntersections,
    curveLineIntersections,
    splitCubicAtT,
)

from typekernel.geo.contour import reverse_contour, signed_area
from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts.caps import HMetrics, _h_record, _o_rec, _polygon
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    Cubic,
    OMetrics,
    _curve,
    _cut,
    _pack,
    _quarters,
    _rev,
    build_o,
)
from typekernel.parts.diagonals import _hwidth
from typekernel.parts.transforms import mirror_x, mirror_y
from typekernel.parts.weight_relief import figure_width_floor, stem_weight_fraction

__all__ = [
    "FIGURE_STEM_RATIO",
    "eight_from_O",
    "five_from_O",
    "four_from_H",
    "nine_from_O",
    "one_from_H",
    "seven_from_H",
    "six_from_O",
    "tabular",
    "three_from_O",
    "two_from_O",
    "zero_from_O",
]

Pt = tuple[float, float]

FIGURE_STEM_RATIO = 0.96
"""Figure stroke over cap stem."""

FIGURE_WIDTH = 0.62
"""Figure ink width over cap height."""


def _fig(H: ComposedGlyph) -> tuple[HMetrics, float, float, float]:
    """``(h, stem, bar, width)`` for figures from the ``H`` record."""
    h = _h_record(H)
    stem = h.stem * FIGURE_STEM_RATIO
    # heavy figures widen so round ones keep a counter
    width = max(FIGURE_WIDTH * h.cap_height, figure_width_floor(stem))
    return h, stem, h.bar * FIGURE_STEM_RATIO, width


def _anchors(width: float, cap: float) -> dict[str, Pt]:
    return {"top": (width / 2.0, cap), "bottom": (width / 2.0, 0.0)}


def zero_from_O(
    O: ComposedGlyph, H: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    """``0``: the ``O`` ring narrowed to figure width, with the figure stroke."""
    c = ctx or O.context
    o = _o_rec(O)
    _, stem, _, w = _fig(H)
    return build_o(
        c,
        replace(o, rx=w / 2.0, thickness_v=stem, thickness_h=stem * c.contrast),
    )


def one_from_H(H: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``1``: a figure stem with a diagonal flag at the top left."""
    c = ctx or H.context
    h, t, bar, w = _fig(H)
    cap = h.cap_height
    wf = stem_weight_fraction(t)
    heavy = max(0.0, wf - 0.45) / 0.55
    s1 = 0.62 * w + t / 2.0
    s0 = s1 - t
    fw = 0.34 * w * (1.0 - 0.2 * heavy)
    fh = 0.2 * cap
    fv = 1.1 * bar * (1.0 - 0.4 * heavy)
    pts = [
        (s0, 0.0),
        (s1, 0.0),
        (s1, cap),
        (s0, cap),
        (s0 - fw, cap - fh),
        (s0 - fw, cap - fh - fv),
        (s0, cap - fv),
    ]
    return _pack(c, h, _anchors(w, cap), _polygon(pts))


def seven_from_H(H: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``7``: a top bar and one compensated diagonal down to the baseline."""
    c = ctx or H.context
    h, t, bar, w = _fig(H)
    cap = h.cap_height
    x_b = 0.22 * w
    hw = _hwidth(t, c.contrast, w - x_b, cap)
    for _ in range(8):
        hw = _hwidth(t, c.contrast, w - hw - x_b, cap)
    # left edge runs parallel to the right one, from (x_b, 0) to (w - hw, cap)
    x_l = x_b + (w - hw - x_b) * (cap - bar) / cap
    pts = [(0.0, cap), (0.0, cap - bar), (x_l, cap - bar), (x_b, 0.0), (x_b + hw, 0.0), (w, cap)]
    return _pack(c, h, _anchors(w, cap), _polygon(pts))


def four_from_H(H: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``4``: a stem, a diagonal from its top to the bar, and the bar; closed counter."""
    c = ctx or H.context
    h, t, bar, w = _fig(H)
    cap = h.cap_height
    w = max(1.06 * w, 3.4 * t)
    s1 = 0.8 * w
    s0 = s1 - t
    yb0 = 0.24 * cap
    yb1 = yb0 + bar
    hw = _hwidth(t, c.contrast, s0, cap - yb1)
    y_meet = yb1 + (s0 - hw) * (cap - yb1) / s0
    if not (0.0 < hw < s0 and yb1 < y_meet < cap):
        raise ValueError("4 strokes do not fit the figure width")
    b = PathBuilder()
    outer = [
        (s0, 0.0),
        (s1, 0.0),
        (s1, yb0),
        (w, yb0),
        (w, yb1),
        (s1, yb1),
        (s1, cap),
        (s0, cap),
        (0.0, yb1),
        (0.0, yb0),
        (s0, yb0),
    ]
    b.moveTo(*outer[0])
    for p in outer[1:]:
        b.lineTo(*p)
    b.closePath()
    b.moveTo(hw, yb1)
    b.lineTo(s0, y_meet)
    b.lineTo(s0, yb1)
    b.closePath()
    return _pack(c, h, _anchors(w, cap), _outer_and_counters(b.build()))


def _outer_and_counters(outline: Outline) -> Outline:
    outer, *rest = outline.contours
    if signed_area(outer) < 0:
        outer = reverse_contour(outer)
    return Outline((outer, *(k if signed_area(k) < 0 else reverse_contour(k) for k in rest)))


def _single_crossing(a: Cubic, b: Cubic) -> Any:
    found: list[Any] = []
    for hit in curveCurveIntersections(list(a), list(b)):
        if (
            0.0 < hit.t1 < 1.0
            and 0.0 < hit.t2 < 1.0
            and all(abs(hit.t1 - k.t1) > 1e-3 for k in found)
        ):
            found.append(hit)
    if len(found) != 1:
        raise ValueError("figure bowls do not cross once; adjust the waist or widths")
    return found[0]


def eight_from_O(
    O: ComposedGlyph,
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    waist: float = 0.54,
    top_scale: float = 0.88,
) -> ComposedGlyph:
    """``8``: two stacked rings sharing the waist stroke, the upper narrower.

    The outer contour follows each ring and switches at their two crossings;
    each ring keeps its own counter.
    """
    c = ctx or O.context
    o: OMetrics = _o_rec(O)
    h, t, bar, w = _fig(H)
    cap, os_, e = h.cap_height, o.overshoot, o.exponent
    tv = min(bar, 0.25 * cap)
    ym = waist * cap
    cx = w / 2.0
    rx_l, rx_u = w / 2.0, top_scale * w / 2.0
    ry_l = (ym + tv / 2.0 + os_) / 2.0
    ry_u = (cap + os_ - (ym - tv / 2.0)) / 2.0
    cy_l, cy_u = ry_l - os_, cap + os_ - ry_u
    th = min(t, 0.6 * rx_u)
    tv = min(tv, 0.6 * min(ry_u, ry_l))
    l0, l1, l2, l3 = _quarters(cx, cy_l, rx_l, ry_l, e)
    u0, u1, u2, u3 = _quarters(cx, cy_u, rx_u, ry_u, e)
    right = _single_crossing(l0, u3)
    left = _single_crossing(l1, u2)
    l0a, _ = splitCubicAtT(*l0, right.t1)
    _, u3b = splitCubicAtT(*u3, right.t2)
    u2a, _ = splitCubicAtT(*u2, left.t2)
    _, l1b = splitCubicAtT(*l1, left.t1)

    b = PathBuilder()
    b.moveTo(*l3[0])
    _curve(b, l3)
    _curve(b, l0a)
    _curve(b, (l0a[3], u3b[1], u3b[2], u3b[3]))
    _curve(b, u0)
    _curve(b, u1)
    _curve(b, u2a)
    _curve(b, (u2a[3], l1b[1], l1b[2], l1b[3]))
    _curve(b, l2)
    b.closePath()
    for qx, qy, rx, ry in ((cx, cy_l, rx_l - th, ry_l - tv), (cx, cy_u, rx_u - th, ry_u - tv)):
        q = _quarters(qx, qy, rx, ry, e)
        b.moveTo(*q[0][0])
        for cubic in q:
            _curve(b, cubic)
        b.closePath()
    return _pack(c, h, _anchors(w, cap), _outer_and_counters(b.build()))


def _line_hits(c: Cubic, p: Pt, q: Pt) -> list[float]:
    """Curve parameters where ``c`` crosses the line through ``p`` and ``q``."""
    far_p = (p[0] - 3.0 * (q[0] - p[0]), p[1] - 3.0 * (q[1] - p[1]))
    far_q = (q[0] + 3.0 * (q[0] - p[0]), q[1] + 3.0 * (q[1] - p[1]))
    found: list[float] = []
    for hit in curveLineIntersections(list(c), [far_p, far_q]):
        if 0.0 < hit.t1 < 1.0 and all(abs(hit.t1 - t) > 1e-3 for t in found):
            found.append(hit.t1)
    return sorted(found)


def _hit(c: Cubic, p: Pt, q: Pt, what: str, *, last: bool) -> float:
    """The first (``last=False``) or last crossing of the line ``p q`` along ``c``.

    A stroke edge may cross a quarter twice (in and out); the splice point
    is the crossing nearest the end of the curve the contour arrives from.
    """
    hits = _line_hits(c, p, q)
    if not hits:
        raise ValueError(f"{what} does not cross its curve; adjust the figure")
    return hits[-1] if last else hits[0]


def _ring_parts(
    cx: float, cy: float, rx: float, ry: float, th: float, tv: float, e: float
) -> tuple[list[Cubic], list[Cubic]]:
    return _quarters(cx, cy, rx, ry, e), _quarters(cx, cy, rx - th, ry - tv, e)


def six_from_O(
    O: ComposedGlyph,
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    bowl: float = 0.6,
    reach: float = 0.55,
) -> ComposedGlyph:
    """``6``: a bowl ring with a straight compensated spine up to cap height.

    The bowl is ``bowl`` × cap high; the spine leaves the ring's upper left and
    ends flat at cap height with its right edge ``reach`` of the way across
    (heavier spines grow to the left, so both edges leave the same quarter).
    Its edges are spliced into the ring's outer curve, so the counter stays
    the bowl's.
    """
    c = ctx or O.context
    o = _o_rec(O)
    h, t, bar, w = _fig(H)
    cap, os_, e = h.cap_height, o.overshoot, o.exponent
    cx, rx = w / 2.0, w / 2.0
    ry = (bowl * cap + os_) / 2.0
    cy = ry - os_
    tv = min(bar, 0.6 * ry)
    th = min(t, 0.6 * rx)
    (q0, q1, q2, q3), inner = _ring_parts(cx, cy, rx, ry, th, tv, e)
    ang = math.radians(140.0)
    start = (cx + (rx - th / 2.0) * math.cos(ang), cy + (ry - tv / 2.0) * math.sin(ang))
    hw = _hwidth(t, c.contrast, reach * w - start[0], cap - start[1])
    end = (reach * w - hw / 2.0, cap)
    # q1 runs from the top to the left: the spine leaves the bowl at the first hit
    t_r = _hit(q1, (start[0] + hw / 2, start[1]), (end[0] + hw / 2, end[1]), "6", last=False)
    t_l = _hit(q1, (start[0] - hw / 2, start[1]), (end[0] - hw / 2, end[1]), "6", last=False)
    if not t_r < t_l:
        raise ValueError("6 spine edges cross the bowl out of order")
    before, _, after = splitCubicAtT(*q1, t_r, t_l)

    b = PathBuilder()
    b.moveTo(*q0[0])
    _curve(b, q0)
    _curve(b, before)
    b.lineTo(end[0] + hw / 2.0, cap)
    b.lineTo(end[0] - hw / 2.0, cap)
    b.lineTo(*after[0])
    for cubic in (after, q2, q3):
        _curve(b, cubic)
    b.closePath()
    b.moveTo(*inner[0][0])
    for cubic in inner:
        _curve(b, cubic)
    b.closePath()
    return _pack(c, h, _anchors(w, cap), _outer_and_counters(b.build()))


def nine_from_O(
    O: ComposedGlyph, H: ComposedGlyph, ctx: DesignContext | None = None
) -> ComposedGlyph:
    """``9``: the ``6`` turned through 180°."""
    six = six_from_O(O, H, ctx)
    box = union_bounds(list(six.solids))
    cx, cy = (box[0] + box[2]) / 2.0, _h_record(H).cap_height / 2.0
    turned = [mirror_y(mirror_x(s, at_x=cx), at_y=cy) for s in six.solids]
    h = _h_record(H)
    w = box[2] - box[0]
    return _pack(ctx or O.context, h, _anchors(w, h.cap_height), *turned)


def two_from_O(
    O: ComposedGlyph,
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    arc: float = 0.58,
    join: float = 0.55,
    aperture: float | None = None,
) -> ComposedGlyph:
    """``2``: an upper arc, a compensated diagonal to the foot, and the base bar.

    The arc (``arc`` × cap high) ends in a vertical terminal on the left; the
    diagonal leaves its lower right — its upper edge cut into the counter
    curve, its lower edge into the outer curve — and lands on the bar.
    """
    c = ctx or O.context
    o = _o_rec(O)
    h, t, bar, w = _fig(H)
    cap, os_, e = h.cap_height, o.overshoot, o.exponent
    cx, rx = w / 2.0, w / 2.0
    ry = (arc * cap + os_) / 2.0
    cy = cap + os_ - ry
    tv = min(bar, 0.6 * ry)
    th = min(t, 0.6 * rx)
    (q0, q1, _, q3), (i0, i1, _, i3) = _ring_parts(cx, cy, rx, ry, th, tv, e)
    ap = max(0.0, min(1.0, c.aperture if aperture is None else aperture))
    x_t = cx - (rx - th) * (0.95 - 0.5 * ap)
    top = _cut(q1, x_t, horizontal=False)[0]
    itop = _cut(i1, x_t, horizontal=False)[0]
    # The diagonal's upper edge meets the counter exactly at ``join`` along its
    # lower-right quarter; the lower edge, one compensated stroke to the right,
    # is cut into the outer curve (q3 runs from the bottom to the right, and
    # coming down the right side the arc meets it at the last crossing).
    foot = (0.0, bar)
    _, in_after = splitCubicAtT(*i3, join)
    j_in = in_after[0]
    hw = _hwidth(t, c.contrast, j_in[0] - foot[0], j_in[1] - foot[1])
    lower = (foot[0] + hw, foot[1]), (j_in[0] + hw, j_in[1])
    t_out = _hit(q3, *lower, "2 diagonal", last=True)
    _, out_after = splitCubicAtT(*q3, t_out)

    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    for p in ((w, 0.0), (w, bar), lower[0], out_after[0]):
        b.lineTo(*p)
    for cubic in (out_after, q0, top):
        _curve(b, cubic)
    b.lineTo(*itop[3])
    for cubic in (_rev(itop), _rev(i0), _rev(in_after)):
        _curve(b, cubic)
    b.lineTo(*foot)
    b.closePath()
    return _pack(c, h, _anchors(w, cap), _outer_and_counters(b.build()))


def three_from_O(
    O: ComposedGlyph,
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    waist: float = 0.55,
    top_scale: float = 0.9,
    top_apex: float = 1.06,
    waist_end: float = 0.15,
    aperture: float | None = None,
) -> ComposedGlyph:
    """``3``: two stacked arcs opening left, sharing a waist stroke that ends in a cut.

    The upper arc is ``top_scale`` × narrower; ``top_apex`` scales the upper
    ellipse height so the cap stays rounded rather than a flat shelf. The waist
    ends ``waist_end`` × the radius left of centre. One contour.
    """
    c = ctx or O.context
    o = _o_rec(O)
    h, t, bar, w = _fig(H)
    cap, os_, e = h.cap_height, o.overshoot, o.exponent
    cx = w / 2.0
    rx_l, rx_u = w / 2.0, top_scale * w / 2.0
    ym = waist * cap
    tv = min(bar, 0.25 * cap)
    ry_l = (ym + tv / 2.0 + os_) / 2.0
    ry_u = (cap + os_ - (ym - tv / 2.0)) / 2.0 * top_apex
    tv = min(tv, 0.6 * min(ry_l, ry_u))
    th = min(t, 0.6 * rx_u)
    cy_l, cy_u = ry_l - os_, cap + os_ - ry_u
    (l0, _, l2, l3), (li0, li1, li2, li3) = _ring_parts(cx, cy_l, rx_l, ry_l, th, tv, e)
    (u0, u1, _, u3), (ui0, ui1, ui2, ui3) = _ring_parts(cx, cy_u, rx_u, ry_u, th, tv, e)
    ap = max(0.0, min(1.0, c.aperture if aperture is None else aperture))
    x_tu = cx - (rx_u - th) * (0.95 - 0.5 * ap)
    x_tl = cx - (rx_l - th) * (0.95 - 0.5 * ap)
    x_w = cx - waist_end * rx_l
    right = _single_crossing(l0, u3)
    l0a, _ = splitCubicAtT(*l0, right.t1)
    _, u3b = splitCubicAtT(*u3, right.t2)
    # Keep the full upper ``u0`` arc (rounded top); open the bowl on the right via ``u1``.
    u_side = _cut(u1, x_tu, horizontal=False)[0]
    ui_side = _cut(ui1, x_tu, horizontal=False)[0]
    l_bot = _cut(l2, x_tl, horizontal=False)[1]
    li_bot = _cut(li2, x_tl, horizontal=False)[1]
    waist_top = _cut(ui2, x_w, horizontal=False)[1]  # x_w → inner bottom of upper
    waist_bot = _cut(li1, x_w, horizontal=False)[0]  # inner top of lower → x_w

    b = PathBuilder()
    b.moveTo(*l_bot[0])
    for cubic in (l_bot, l3, l0a, (l0a[3], u3b[1], u3b[2], u3b[3]), u0, u_side):
        _curve(b, cubic)
    b.lineTo(*ui_side[3])
    for cubic in (_rev(ui_side), _rev(ui0), _rev(ui3), _rev(waist_top)):
        _curve(b, cubic)
    b.lineTo(*waist_bot[3])
    for cubic in (_rev(waist_bot), _rev(li0), _rev(li3), _rev(li_bot)):
        _curve(b, cubic)
    b.closePath()
    return _pack(c, h, _anchors(w, cap), _outer_and_counters(b.build()))


def five_from_O(
    O: ComposedGlyph,
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    bowl: float = 0.62,
    seat: float = 0.55,
    aperture: float | None = None,
) -> ComposedGlyph:
    """``5``: a top bar, a vertical stem, and a bowl opening at the lower left.

    The stem's flat foot sits on the bowl's counter at ``seat`` of its upper
    half; its right face meets the bowl's outer curve. One contour.
    """
    c = ctx or O.context
    o = _o_rec(O)
    h, t, bar, w = _fig(H)
    cap, os_, e = h.cap_height, o.overshoot, o.exponent
    relief = min(1.0, max(0.0, (c.stem - 45.0) / 130.0))
    w *= 1.028 + 0.15 * relief
    cx, rx = w / 2.0, w / 2.0
    bowl_eff = bowl - 0.035 * relief
    ry = (bowl_eff * cap + os_) / 2.0
    cy = ry - os_
    stroke_scale = (1.0 - 0.13 * relief) * (0.972 + 0.008 * relief)
    tv = min(bar, 0.6 * ry) * stroke_scale
    th = min(t, 0.6 * rx) * stroke_scale
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring_parts(cx, cy, rx, ry, th, tv, e)
    y_seat = cy + seat * (ry - tv)
    i_seat = _cut(i1, y_seat, horizontal=True)  # inner top → seat → inner left
    s1 = i_seat[0][3][0]
    s0 = s1 - t
    o_join = _cut(q1, s1, horizontal=False)  # outer top → stem face → outer left
    ap = max(0.0, min(1.0, c.aperture if aperture is None else aperture))
    ap_eff = min(1.0, ap + 0.12 * relief)
    x_t = cx - (rx - th) * (0.95 - 0.5 * ap_eff)
    l_bot = _cut(q2, x_t, horizontal=False)[1]
    li_bot = _cut(i2, x_t, horizontal=False)[1]
    if not o_join[0][3][1] < cap - bar:
        raise ValueError("5 bowl reaches the top bar; lower the bowl")

    b = PathBuilder()
    b.moveTo(s0, cap)
    b.lineTo(s0, y_seat)
    b.lineTo(s1, y_seat)
    for cubic in (i_seat[0], i0, i3, li_bot):
        _curve(b, _rev(cubic))
    b.lineTo(*l_bot[0])
    for cubic in (l_bot, q3, q0, o_join[0]):
        _curve(b, cubic)
    for p in ((s1, cap - bar), (w, cap - bar), (w, cap)):
        b.lineTo(*p)
    b.closePath()
    return _pack(c, h, _anchors(w, cap), _outer_and_counters(b.build()))


def tabular(
    glyphs: dict[str, ComposedGlyph], advance: float | None = None
) -> dict[str, ComposedGlyph]:
    """Give every glyph one advance (the widest, or ``advance``), ink centred.

    Use on figures for columns of numbers; proportional spacing stays the
    default elsewhere.
    """
    if not glyphs:
        return {}
    target = max(g.advance for g in glyphs.values()) if advance is None else advance
    out: dict[str, ComposedGlyph] = {}
    for ch, g in glyphs.items():
        box = union_bounds(list(g.solids) + list(g.holes))
        ink = box[2] - box[0]
        moved = g.translated((target - ink) / 2.0 - box[0])
        out[ch] = replace(moved, advance=target)
    return out
