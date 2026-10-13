"""Capitals — control ``H`` and ``O``, and the forms that derive from them.

Capitals get their own design records: the cap stem is a touch heavier than
the lowercase stem (caps are bigger shapes and would otherwise look light
next to ``n``), and widths / crossbar height belong to the ``H``. Every
capital derives from the drawn ``H`` (stems, bars, width) and ``O`` (bowls)
the same way the lowercase derives from ``n`` and ``o``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from fontTools.misc.bezierTools import curveLineIntersections, splitCubicAtT

from typekernel.geo.contour import reverse_contour
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import (
    Cubic,
    NMetrics,
    OMetrics,
    _ccw,
    _curve,
    _cut,
    _pack,
    _quarters,
    _rev,
    _ring,
    _terminal_x,
    build_o,
    c_from_o,
    n_metrics,
    o_metrics,
    s_from_o,
)
from typekernel.parts.diagonals import _hwidth

__all__ = [
    "C_from_O",
    "D_from_H",
    "E_from_H",
    "F_from_H",
    "G_from_O",
    "HMetrics",
    "I_from_H",
    "J_from_H",
    "L_from_H",
    "Q_from_O",
    "S_from_O",
    "T_from_H",
    "U_from_H",
    "build_H",
    "build_O",
    "cap_o_metrics",
    "h_cap_metrics",
]

Pt = tuple[float, float]

CAP_STEM_RATIO = 1.08
"""Cap stem over lowercase stem."""


@dataclass(frozen=True, slots=True)
class HMetrics:
    """Design record for the straight capitals (``H I L E F T`` …).

    Attributes:
        stem: Vertical cap stem.
        bar: Horizontal stroke thickness (crossbars, arms).
        cap_height: Flat top of the capitals.
        width: Ink width of ``H``, stem to stem.
        bar_y: Centre of the ``H`` crossbar (optically a little above centre).
        overshoot: Round / pointed capitals pass the zones by this much.
    """

    stem: float
    bar: float
    cap_height: float
    width: float
    bar_y: float
    overshoot: float

    def tuned(self, **kwargs: float) -> HMetrics:
        return replace(self, **kwargs)


def h_cap_metrics(ctx: DesignContext, n: NMetrics | None = None) -> HMetrics:
    """Derive the ``H`` record from family proportions and the ``n`` stem."""
    stem = (n or n_metrics(ctx)).stem * CAP_STEM_RATIO
    return HMetrics(
        stem=stem,
        bar=stem * ctx.contrast * 0.92,
        cap_height=ctx.cap_height,
        width=ctx.cap_height * (0.70 + 0.12 * ctx.aperture),
        bar_y=ctx.cap_height * 0.52,
        overshoot=ctx.overshoot,
    )


def cap_o_metrics(ctx: DesignContext, n: NMetrics | None = None) -> OMetrics:
    """The ``O`` record: the ``o`` construction at cap height with the cap stem."""
    lower = o_metrics(ctx)
    ry = ctx.cap_height / 2.0 + ctx.overshoot
    return OMetrics(
        rx=ry * (0.90 + 0.10 * ctx.aperture),
        ry=ry,
        thickness=(n or n_metrics(ctx)).stem * CAP_STEM_RATIO,
        exponent=lower.exponent,
        x_height=ctx.cap_height,
        overshoot=ctx.overshoot,
    )


def _h_record(glyph: ComposedGlyph) -> HMetrics:
    return glyph.design if isinstance(glyph.design, HMetrics) else h_cap_metrics(glyph.context)


def _polygon(points: list[Pt]) -> Outline:
    b = PathBuilder()
    b.moveTo(*points[0])
    for p in points[1:]:
        b.lineTo(*p)
    b.closePath()
    return _ccw(b.build())


def _cap_anchors(width: float, h: HMetrics) -> dict[str, Pt]:
    return {"top": (width / 2.0, h.cap_height), "bottom": (width / 2.0, 0.0)}


def build_H(ctx: DesignContext, metrics: HMetrics | None = None) -> ComposedGlyph:
    """Control ``H``: two cap stems and a crossbar, one contour."""
    h = metrics or h_cap_metrics(ctx)
    t, w, cap = h.stem, h.width, h.cap_height
    y0, y1 = h.bar_y - h.bar / 2.0, h.bar_y + h.bar / 2.0
    pts = [
        (0.0, 0.0),
        (t, 0.0),
        (t, y0),
        (w - t, y0),
        (w - t, 0.0),
        (w, 0.0),
        (w, cap),
        (w - t, cap),
        (w - t, y1),
        (t, y1),
        (t, cap),
        (0.0, cap),
    ]
    return _pack(ctx, h, _cap_anchors(w, h), _polygon(pts))


def build_O(ctx: DesignContext, metrics: OMetrics | None = None) -> ComposedGlyph:
    """Control ``O``: the ``o`` ring drawn at cap height with the cap stem."""
    return build_o(ctx, metrics or cap_o_metrics(ctx))


def I_from_H(H: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``I``: one ``H`` stem."""
    c = ctx or H.context
    h = _h_record(H)
    pts = [(0.0, 0.0), (h.stem, 0.0), (h.stem, h.cap_height), (0.0, h.cap_height)]
    return _pack(c, h, _cap_anchors(h.stem, h), _polygon(pts))


def L_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.78,
) -> ComposedGlyph:
    """``L``: the ``H`` stem with a foot ``width`` × the ``H`` width."""
    c = ctx or H.context
    h = _h_record(H)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    pts = [(0.0, 0.0), (w, 0.0), (w, bt), (t, bt), (t, cap), (0.0, cap)]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


def E_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.84,
) -> ComposedGlyph:
    """``E``: stem with three arms; the middle arm is shorter, the foot longest."""
    c = ctx or H.context
    h = _h_record(H)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid, w_bot = w * 0.97, w * 0.88, w
    m0, m1 = h.bar_y - bt / 2.0, h.bar_y + bt / 2.0
    pts = [
        (0.0, 0.0),
        (w_bot, 0.0),
        (w_bot, bt),
        (t, bt),
        (t, m0),
        (w_mid, m0),
        (w_mid, m1),
        (t, m1),
        (t, cap - bt),
        (w_top, cap - bt),
        (w_top, cap),
        (0.0, cap),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


def F_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.82,
) -> ComposedGlyph:
    """``F``: the ``E`` without its foot; the middle arm sits a little lower."""
    c = ctx or H.context
    h = _h_record(H)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid = w, w * 0.9
    mid = h.bar_y - 0.03 * cap
    m0, m1 = mid - bt / 2.0, mid + bt / 2.0
    pts = [
        (0.0, 0.0),
        (t, 0.0),
        (t, m0),
        (w_mid, m0),
        (w_mid, m1),
        (t, m1),
        (t, cap - bt),
        (w_top, cap - bt),
        (w_top, cap),
        (0.0, cap),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


def _o_rec(O: ComposedGlyph) -> OMetrics:
    return O.design if isinstance(O.design, OMetrics) else cap_o_metrics(O.context)


def C_from_O(O: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``C``: the lowercase ``c`` construction on the cap ``O``."""
    return c_from_o(O, ctx)


def S_from_O(O: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``S``: the lowercase ``s`` construction on the cap ``O``, a little wider."""
    return s_from_o(O, ctx, width=0.86)


def G_from_O(
    O: ComposedGlyph,
    H: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    bar_reach: float = 0.1,
) -> ComposedGlyph:
    """``G``: the ``C`` whose lower arm rises into an inward crossbar.

    The right wall continues up to just under the centre, then turns into a
    horizontal bar (the ``H`` bar thickness) reaching ``bar_reach`` × the
    radius past the centre. One contour.
    """
    c = ctx or O.context
    o = _o_rec(O)
    h = _h_record(H) if H is not None else h_cap_metrics(c)
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o)
    cx, cy = o.rx, o.x_height / 2.0
    x_t = _terminal_x(o, c.aperture, 0.55)
    top = _cut(q0, x_t, horizontal=False)[1]
    itop = _cut(i0, x_t, horizontal=False)[1]
    bar_top = cy - 0.02 * o.x_height
    bar_bot = bar_top - min(h.bar, 0.8 * (o.ry - o.thickness))
    lower = _cut(q3, bar_top, horizontal=True)[0]
    ilower = _cut(i3, bar_bot, horizontal=True)[0]
    x_bar = cx + bar_reach * o.rx

    b = PathBuilder()
    b.moveTo(*top[0])
    for cubic in (top, q1, q2, lower):
        _curve(b, cubic)
    b.lineTo(x_bar, bar_top)
    b.lineTo(x_bar, bar_bot)
    b.lineTo(*ilower[3])
    for cubic in (_rev(ilower), _rev(i2), _rev(i1), _rev(itop)):
        _curve(b, cubic)
    b.closePath()
    return _pack(c, o, _cap_anchors(2.0 * o.rx, h), _ccw(b.build()))


def Q_from_O(
    O: ComposedGlyph,
    H: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
) -> ComposedGlyph:
    """``Q``: the ``O`` with a compensated diagonal tail from its lower right.

    The tail's two edges are intersected with the bowl's lower-right outer
    quarter and spliced in, so the outer contour grows the tail and the
    counter stays the ``O``'s — no overlap, no boolean, fixed topology.
    """
    c = ctx or O.context
    o = _o_rec(O)
    h = _h_record(H) if H is not None else h_cap_metrics(c)
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o)
    cx, cy = o.rx, o.x_height / 2.0
    # tail axis: from inside the wall (centreline, -45°) out past the bottom right
    k = math.cos(math.radians(45.0))
    start = (cx + (o.rx - o.thickness / 2.0) * k, cy - (o.ry - o.thickness / 2.0) * k)
    end = (cx + 1.0 * o.rx, -o.overshoot - 0.1 * o.x_height)
    hw = _hwidth(h.stem * 0.95, c.contrast, end[0] - start[0], start[1] - end[1])
    hits: list[float] = []
    for side in (-0.5, 0.5):
        a = (start[0] + side * hw, start[1])
        z = (end[0] + side * hw, end[1])
        far = (a[0] - (z[0] - a[0]), a[1] - (z[1] - a[1]))
        found = [i.t1 for i in curveLineIntersections(list(q3), [far, z]) if 0.0 < i.t1 < 1.0]
        if len(found) != 1:
            raise ValueError("Q tail does not meet the bowl once per edge; adjust the O")
        hits.append(found[0])
    t_lo, t_hi = sorted(hits)
    before, _, after = splitCubicAtT(*q3, t_lo, t_hi)

    b = PathBuilder()
    b.moveTo(*q0[0])
    for cubic in (q0, q1, q2, before):
        _curve(b, cubic)
    b.lineTo(end[0] - hw / 2.0, end[1])
    b.lineTo(end[0] + hw / 2.0, end[1])
    b.lineTo(*after[0])
    _curve(b, after)
    b.closePath()
    b.moveTo(*i0[0])
    for cubic in (i0, i1, i2, i3):
        _curve(b, cubic)
    b.closePath()
    outer, counter = b.build().contours
    return _pack(c, o, _cap_anchors(2.0 * o.rx, h), Outline((outer, reverse_contour(counter))))


def D_from_H(
    H: ComposedGlyph,
    O: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    width: float = 1.05,
    straight: float = 0.4,
) -> ComposedGlyph:
    """``D``: the ``H`` stem and flat top / foot turning into a half bowl.

    ``width`` × the ``H`` width; the bowl starts ``straight`` of the way
    across. Top and foot are flat strokes (no overshoot); the bowl's right
    side carries the ``O`` superellipse exponent. Outer + counter.
    """
    c = ctx or H.context
    h = _h_record(H)
    e = _o_rec(O).exponent if O is not None else cap_o_metrics(c).exponent
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    x0 = straight * w
    cy = cap / 2.0
    _, _, _, q3 = _quarters(x0, cy, w - x0, cy, e)
    q0 = _quarters(x0, cy, w - x0, cy, e)[0]
    _, _, _, i3 = _quarters(x0, cy, w - x0 - t, cy - bt, e)
    i0 = _quarters(x0, cy, w - x0 - t, cy - bt, e)[0]

    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(x0, 0.0)
    _curve(b, q3)
    _curve(b, q0)
    b.lineTo(0.0, cap)
    b.closePath()
    b.moveTo(t, bt)
    b.lineTo(t, cap - bt)
    b.lineTo(x0, cap - bt)
    _curve(b, _rev(i0))
    _curve(b, _rev(i3))
    b.closePath()
    outer, counter = b.build().contours
    return _pack(c, h, _cap_anchors(w, h), _ccw(Outline((outer, counter))))


_MIN_BOWL_STEMS = 2.3
"""Heavy ``U`` / ``J`` widen so the bowl keeps a counter between its walls."""


def _u_parts(h: HMetrics, w: float, e: float, spring: float) -> tuple[Cubic, ...]:
    """Bottom bowl quarters for ``U`` / ``J``: outer q2, q3 and inner i2, i3."""
    cx = w / 2.0
    ry = spring + h.overshoot
    ry_i = ry - h.bar
    _, _, q2, q3 = _quarters(cx, spring, w / 2.0, ry, e)
    _, _, i2, i3 = _quarters(cx, spring, w / 2.0 - h.stem, ry_i, e)
    return q2, q3, i2, i3


def U_from_H(
    H: ComposedGlyph,
    O: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.96,
    spring: float = 0.38,
) -> ComposedGlyph:
    """``U``: two ``H`` stems joined by the bottom half of a bowl.

    The bowl springs at ``spring`` × cap height and overshoots the baseline;
    its bottom is as thick as the ``H`` bar. One contour.
    """
    c = ctx or H.context
    h = _h_record(H)
    e = _o_rec(O).exponent if O is not None else cap_o_metrics(c).exponent
    t, cap = h.stem, h.cap_height
    w = max(width * h.width, _MIN_BOWL_STEMS * t)
    y_s = spring * cap
    q2, q3, i2, i3 = _u_parts(h, w, e, y_s)

    b = PathBuilder()
    b.moveTo(0.0, cap)
    b.lineTo(0.0, y_s)
    _curve(b, q2)
    _curve(b, q3)
    b.lineTo(w, cap)
    b.lineTo(w - t, cap)
    b.lineTo(w - t, y_s)
    _curve(b, _rev(i3))
    _curve(b, _rev(i2))
    b.lineTo(t, cap)
    b.closePath()
    return _pack(c, h, _cap_anchors(w, h), _ccw(b.build()))


def J_from_H(
    H: ComposedGlyph,
    O: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.72,
    spring: float = 0.38,
    hook: float = 0.55,
) -> ComposedGlyph:
    """``J``: the right half of ``U`` with its bowl ending in a vertical terminal.

    ``hook`` places the terminal between the bowl centre (``0``) and its
    left side (``1``).
    """
    c = ctx or H.context
    h = _h_record(H)
    e = _o_rec(O).exponent if O is not None else cap_o_metrics(c).exponent
    t, cap = h.stem, h.cap_height
    w = max(width * h.width, _MIN_BOWL_STEMS * t)
    y_s = spring * cap
    q2, q3, i2, i3 = _u_parts(h, w, e, y_s)
    cx = w / 2.0
    x_t = cx - hook * (w / 2.0 - t)
    outer = _cut(q2, x_t, horizontal=False)[1]
    inner = _cut(i2, x_t, horizontal=False)[1]

    b = PathBuilder()
    b.moveTo(w, cap)
    b.lineTo(w - t, cap)
    b.lineTo(w - t, y_s)
    _curve(b, _rev(i3))
    _curve(b, _rev(inner))
    b.lineTo(*outer[0])
    _curve(b, outer)
    _curve(b, q3)
    b.closePath()
    return _pack(c, h, {"top": (w - t / 2.0, cap), "bottom": (cx, 0.0)}, _ccw(b.build()))


def T_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.92,
) -> ComposedGlyph:
    """``T``: an ``H`` stem centred under a top bar ``width`` × the ``H`` width."""
    c = ctx or H.context
    h = _h_record(H)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    s0, s1 = (w - t) / 2.0, (w + t) / 2.0
    pts = [
        (s0, 0.0),
        (s1, 0.0),
        (s1, cap - bt),
        (w, cap - bt),
        (w, cap),
        (0.0, cap),
        (0.0, cap - bt),
        (s0, cap - bt),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))
