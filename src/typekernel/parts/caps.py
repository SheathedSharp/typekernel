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
from typing import Any

from fontTools.misc.bezierTools import (
    cubicPointAtT,
    curveCurveIntersections,
    curveLineIntersections,
    splitCubicAtT,
)

from typekernel.geo.contour import reverse_contour, signed_area
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import KAPPA
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
from typekernel.parts.diagonals import _hwidth, k_points, v_points, w_points, x_points, z_points
from typekernel.parts.terminal_openings import apply_terminal_shear, opening_closure
from typekernel.parts.weight_relief import min_bowl_stems

__all__ = [
    "A_from_H",
    "B_from_H",
    "C_from_O",
    "D_from_H",
    "E_from_H",
    "F_from_H",
    "G_from_O",
    "HMetrics",
    "I_from_H",
    "J_from_H",
    "K_from_H",
    "L_from_H",
    "M_from_H",
    "N_from_H",
    "P_from_H",
    "Q_from_O",
    "R_from_H",
    "S_from_O",
    "T_from_H",
    "U_from_H",
    "V_from_H",
    "W_from_H",
    "X_from_H",
    "Y_from_H",
    "Z_from_H",
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
    cap_stem = (n or n_metrics(ctx)).stem * CAP_STEM_RATIO
    return OMetrics(
        rx=ry * (0.90 + 0.10 * ctx.aperture),
        ry=ry,
        thickness_v=cap_stem,
        thickness_h=cap_stem * ctx.contrast,
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
    from typekernel.parts.primitives import contrast_stem_caps

    stem = contrast_stem_caps(c, 0.0, 0.0, h.cap_height, width=h.stem)
    return _pack(c, h, _cap_anchors(h.stem, h), stem)


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
    outline = apply_terminal_shear(c, _polygon(pts), at=(w_top, cap - bt * 0.5))
    return _pack(c, h, _cap_anchors(w, h), outline)


def _o_rec(O: ComposedGlyph) -> OMetrics:
    return O.design if isinstance(O.design, OMetrics) else cap_o_metrics(O.context)


def C_from_O(
    O: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    aperture: float | None = None,
) -> ComposedGlyph:
    """``C``: the lowercase ``c`` construction on the cap ``O``."""
    if aperture is None:
        return c_from_o(O, ctx)
    return c_from_o(O, ctx, aperture=aperture)


def S_from_O(
    O: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.86,
) -> ComposedGlyph:
    """``S``: the lowercase ``s`` construction on the cap ``O``, a little wider."""
    return s_from_o(O, ctx, width=width)


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
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o, c)
    cx, cy = o.rx, o.x_height / 2.0
    x_t = _terminal_x(o, c.aperture, opening_closure(c, 0.55))
    top = _cut(q0, x_t, horizontal=False)[1]
    itop = _cut(i0, x_t, horizontal=False)[1]
    bar_top = cy - 0.02 * o.x_height
    bar_bot = bar_top - min(h.bar, 0.8 * (o.ry - o.thickness_h))
    lower = _cut(q3, bar_top, horizontal=True)[0]
    ilower = _cut(i3, bar_bot, horizontal=True)[0]
    x_bar = cx + bar_reach * o.rx
    bar_h = bar_top - bar_bot
    chamfer = min(h.stem * 0.32, bar_h * 0.48, 0.07 * o.x_height)

    b = PathBuilder()
    b.moveTo(*top[0])
    for cubic in (top, q1, q2, lower):
        _curve(b, cubic)
    b.lineTo(x_bar, bar_top)
    use = max(h.stem * 0.055, min(chamfer, bar_h * 0.5))
    if h.stem > 180.0:
        use = min(use, 0.34)
    b.lineTo(x_bar, bar_bot + use)
    b.curveTo(
        x_bar,
        bar_bot,
        x_bar + use * KAPPA,
        bar_bot,
        x_bar + use,
        bar_bot - use * (1.0 - KAPPA),
    )
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
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o, c)
    cx, cy = o.rx, o.x_height / 2.0
    # tail axis: from inside the wall (centreline, -45°) out past the bottom right
    k = math.cos(math.radians(45.0))
    start = (cx + (o.rx - o.thickness_v / 2.0) * k, cy - (o.ry - o.thickness_h / 2.0) * k)
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
    w = max(width * h.width, min_bowl_stems(t) * t + 0.3 * t)
    x0 = _straight_run(straight, w, t)
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


"""Heavy bowl capitals widen via :func:`~typekernel.parts.weight_relief.min_bowl_stems`."""


def _straight_run(straight: float, width: float, stem: float) -> float:
    """Where a stem + half bowl's flat top / foot turn round: past the stem."""
    return max(straight * width, 1.2 * stem)


def _half_bowl(
    x0: float, y0: float, y1: float, right: float, stem: float, bar: float, e: float
) -> tuple[Cubic, Cubic, Cubic, Cubic]:
    """Right half of a flattened bowl spanning ``y0..y1`` from ``x0`` to ``right``.

    Returns outer ``(q3, q0)`` and counter ``(i3, i0)`` quarters; the bowl's
    top and bottom strokes are ``bar`` thick, its round side ``stem`` thick.
    """
    cy, ry = (y0 + y1) / 2.0, (y1 - y0) / 2.0
    q0, _, _, q3 = _quarters(x0, cy, right - x0, ry, e)
    i0, _, _, i3 = _quarters(x0, cy, right - x0 - stem, ry - bar, e)
    return q3, q0, i3, i0


def _counter(b: PathBuilder, t: float, x0: float, i3: Cubic, i0: Cubic) -> None:
    """Counter of a stem + half bowl: stem face, flat top, round side, flat foot."""
    b.moveTo(t, i3[0][1])
    b.lineTo(t, i0[3][1])
    b.lineTo(x0, i0[3][1])
    _curve(b, _rev(i0))
    _curve(b, _rev(i3))
    b.closePath()


def _with_counters(b: PathBuilder) -> Outline:
    """Outer first (made CCW), every later contour turned clockwise."""
    outer, *rest = b.build().contours
    if signed_area(outer) < 0:
        outer = reverse_contour(outer)
    return Outline((outer, *(k if signed_area(k) < 0 else reverse_contour(k) for k in rest)))


def _bowl_cap_setup(
    H: ComposedGlyph, O: ComposedGlyph | None, ctx: DesignContext | None
) -> tuple[DesignContext, HMetrics, float]:
    c = ctx or H.context
    h = _h_record(H)
    e = _o_rec(O).exponent if O is not None else cap_o_metrics(c).exponent
    return c, h, e


def P_from_H(
    H: ComposedGlyph,
    O: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.9,
    straight: float = 0.45,
    bowl: float = 0.47,
) -> ComposedGlyph:
    """``P``: the ``H`` stem with a half bowl from ``bowl`` × cap height up."""
    c, h, e = _bowl_cap_setup(H, O, ctx)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = max(width * h.width, min_bowl_stems(t) * t)
    x0, y_b = _straight_run(straight, w, t), bowl * cap - bt / 2.0
    q3, q0, i3, i0 = _half_bowl(x0, y_b, cap, w, t, bt, e)
    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    for p in ((t, 0.0), (t, y_b), (x0, y_b)):
        b.lineTo(*p)
    _curve(b, q3)
    _curve(b, q0)
    b.lineTo(0.0, cap)
    b.closePath()
    _counter(b, t, x0, i3, i0)
    return _pack(c, h, _cap_anchors(w, h), _with_counters(b))


def R_from_H(
    H: ComposedGlyph,
    O: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.94,
    straight: float = 0.45,
    bowl: float = 0.47,
    leg_at: float = 0.3,
) -> ComposedGlyph:
    """``R``: the ``P`` with a compensated leg from the bowl to the baseline.

    The leg's right edge runs from the foot corner to the point ``leg_at``
    along the bowl's lower curve (an exact splice); its left edge, one
    compensated stroke to the left, lands on the bowl's flat foot.
    """
    c, h, e = _bowl_cap_setup(H, O, ctx)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = max(width * h.width, min_bowl_stems(t) * t)
    bowl_w = 0.96 * w
    x0, y_b = _straight_run(straight, bowl_w, t), bowl * cap - bt / 2.0
    q3, q0, i3, i0 = _half_bowl(x0, y_b, cap, bowl_w, t, bt, e)
    foot_r = (w, 0.0)
    lo, hi, t_c = 0.0, 1.0, leg_at
    for _ in range(40):
        pc = cubicPointAtT(*q3, t_c)
        hw = _hwidth(h.stem * 0.95, c.contrast, w - pc[0], pc[1])
        x_l = (w - hw) + (pc[0] - w) * (y_b / pc[1])
        if x_l > x0:
            hi, t_c = t_c, (lo + t_c) / 2.0
        elif x_l < t:
            lo, t_c = t_c, (t_c + hi) / 2.0
        else:
            break
    else:
        raise ValueError("R leg does not fit between stem and bowl; adjust width")
    _, after = splitCubicAtT(*q3, t_c)

    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    for p in ((t, 0.0), (t, y_b), (x_l, y_b), (w - hw, 0.0), foot_r, after[0]):
        b.lineTo(*p)
    _curve(b, after)
    _curve(b, q0)
    b.lineTo(0.0, cap)
    b.closePath()
    _counter(b, t, x0, i3, i0)
    return _pack(c, h, _cap_anchors(w, h), _with_counters(b))


def B_from_H(
    H: ComposedGlyph,
    O: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.92,
    top_scale: float = 0.9,
    straight: float = 0.45,
    waist: float = 0.53,
) -> ComposedGlyph:
    """``B``: the ``H`` stem with two stacked half bowls, the upper narrower.

    The bowls share the middle bar at ``waist`` × cap height; the outer
    notch between them is the intersection of their curves.
    """
    c, h, e = _bowl_cap_setup(H, O, ctx)
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = max(width * h.width, min_bowl_stems(t) * t / top_scale)
    wu = top_scale * w
    m1 = waist * cap + bt / 2.0
    m0 = m1 - bt
    xl, xu = _straight_run(straight, w, t), _straight_run(straight, wu, t)
    lq3, lq0, li3, li0 = _half_bowl(xl, 0.0, m1, w, t, bt, e)
    uq3, uq0, ui3, ui0 = _half_bowl(xu, m0, cap, wu, t, bt, e)
    inside: list[Any] = []
    for hit in curveCurveIntersections(list(lq0), list(uq3)):
        # fontTools may report one crossing twice; merge near-identical hits
        if (
            0.0 < hit.t1 < 1.0
            and 0.0 < hit.t2 < 1.0
            and all(abs(hit.t1 - k.t1) > 1e-3 for k in inside)
        ):
            inside.append(hit)
    if len(inside) != 1:
        raise ValueError("B bowls do not cross once; adjust top_scale or waist")
    low_part, _ = splitCubicAtT(*lq0, inside[0].t1)
    _, up_part = splitCubicAtT(*uq3, inside[0].t2)

    b = PathBuilder()
    b.moveTo(0.0, 0.0)
    b.lineTo(xl, 0.0)
    _curve(b, lq3)
    _curve(b, low_part)
    _curve(b, (low_part[3], up_part[1], up_part[2], up_part[3]))
    _curve(b, uq0)
    b.lineTo(0.0, cap)
    b.closePath()
    _counter(b, t, xl, li3, li0)
    _counter(b, t, xu, ui3, ui0)
    return _pack(c, h, _cap_anchors(w, h), _with_counters(b))


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
    w = max(width * h.width, min_bowl_stems(t) * t)
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
    w = max(width * h.width, min_bowl_stems(t) * t)
    y_s = spring * cap
    q2, q3, i2, i3 = _u_parts(h, w, e, y_s)
    cx = w / 2.0
    hook = hook * (opening_closure(c, 0.55) / 0.55)
    x_t = cx - hook * (w / 2.0 - t)
    outer = _cut(q2, x_t, horizontal=False)[1]
    inner = _cut(i2, x_t, horizontal=False)[1]

    b = PathBuilder()
    b.moveTo(w, cap)
    b.lineTo(w - t, cap)
    b.lineTo(w - t, y_s)
    _curve(b, _rev(i3))
    _curve(b, _rev(inner))
    bulge = max(t * 0.09, 5.0)
    ji, jo = inner[0], outer[0]
    b.curveTo(
        ji[0] - bulge * 0.4,
        ji[1] - bulge * 0.12,
        jo[0],
        jo[1] + bulge * 0.18,
        jo[0],
        jo[1],
    )
    _curve(b, outer)
    _curve(b, q3)
    b.closePath()
    return _pack(c, h, {"top": (w - t / 2.0, cap), "bottom": (cx, 0.0)}, _ccw(b.build()))


def _diag_cap(
    H: ComposedGlyph, ctx: DesignContext | None, width: float, pts: list[Pt]
) -> ComposedGlyph:
    c = ctx or H.context
    h = _h_record(H)
    return _pack(c, h, _cap_anchors(width, h), _polygon(pts))


def V_from_H(
    H: ComposedGlyph, ctx: DesignContext | None = None, *, width: float = 0.98
) -> ComposedGlyph:
    """``V``: the ``v`` construction at cap height with the cap stem."""
    h, c = _h_record(H), ctx or H.context
    w_frac = width
    s = c.stem
    if s <= 72.0 and (
        0.95 <= c.contrast < 1.0
        or (c.contrast >= 1.0 and c.roundness < 0.26)
    ):
        w_frac += 0.02
    if 142.0 <= s <= 158.0:
        w_frac += 0.04
    w = w_frac * h.width
    bump = c.sharp_overshoot
    return _diag_cap(
        H, ctx, w, v_points(h.stem, h.cap_height, w, c.contrast, top_overshoot=bump)
    )


def W_from_H(
    H: ComposedGlyph, ctx: DesignContext | None = None, *, width: float = 1.4
) -> ComposedGlyph:
    """``W``: the ``w`` construction at cap height (four lighter diagonals)."""
    h, c = _h_record(H), ctx or H.context
    w_frac = width
    s = c.stem
    if s <= 72.0:
        if c.contrast < 0.85:
            w_frac += 0.02
        elif 0.86 <= c.contrast <= 0.94 and c.aperture < 0.68:
            w_frac -= 0.02
    if 168.0 <= s <= 192.0:
        w_frac += 0.02
    w = w_frac * h.width
    bump = c.sharp_overshoot
    return _diag_cap(
        H,
        ctx,
        w,
        w_points(h.stem, h.cap_height, w, c.contrast, top_overshoot=bump),
    )


def X_from_H(
    H: ComposedGlyph, ctx: DesignContext | None = None, *, width: float = 0.92
) -> ComposedGlyph:
    """``X``: two compensated diagonals crossing at mid cap height."""
    h, c = _h_record(H), ctx or H.context
    w_frac = width
    if 100.0 <= c.stem <= 118.0:
        w_frac += 0.011
    w = w_frac * h.width
    return _diag_cap(H, ctx, w, x_points(h.stem, h.cap_height, w, c.contrast))


def Z_from_H(
    H: ComposedGlyph, ctx: DesignContext | None = None, *, width: float = 0.88
) -> ComposedGlyph:
    """``Z``: ``H``-bar-thick top and foot joined by one compensated diagonal."""
    h, c = _h_record(H), ctx or H.context
    w = width * h.width
    return _diag_cap(H, ctx, w, z_points(h.stem, h.bar, h.cap_height, w, c.contrast))


def K_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.92,
    vertex: float = 0.42,
) -> ComposedGlyph:
    """``K``: the ``H`` stem with arm and leg meeting at the stem; the arm reaches cap height."""
    h, c = _h_record(H), ctx or H.context
    s = c.stem
    w_frac = width
    vertex_eff = vertex
    if s <= 72.0:
        w_frac += 0.07
    elif s < 80.0:
        w_frac += 0.07 * max(0.0, (80.0 - s) / 50.0)
    if 100.0 <= s <= 118.0:
        w_frac += 0.038
        vertex_eff = max(vertex_eff, 0.44)
    if 142.0 <= s <= 158.0:
        w_frac += 0.024
    if 168.0 <= s <= 192.0:
        w_frac += 0.042
    w = w_frac * h.width
    cap = h.cap_height
    return _diag_cap(
        H, c, w, k_points(h.stem, cap, cap, w, c.contrast, vertex=vertex_eff)
    )


def A_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 1.02,
    apex: float = 0.35,
    bar: float = 0.28,
) -> ComposedGlyph:
    """``A``: the ``V`` turned over, with a crossbar at ``bar`` × cap height.

    Outer contour plus the triangular counter above the bar.
    """
    c = ctx or H.context
    h = _h_record(H)
    # heavy A widens so the counter above the bar stays open
    w, cap = max(width * h.width, 3.2 * h.stem), h.cap_height
    peak = cap + c.sharp_overshoot
    f = apex * h.stem
    a = (w - f) / 2.0
    hw = _hwidth(h.stem, c.contrast, a, cap)
    crotch = cap * (w - 2.0 * hw) / (2.0 * a)
    y0 = bar * cap - h.bar / 2.0
    y1 = min(y0 + h.bar, crotch - 0.5 * h.stem)
    if not (hw > f / 2.0 and 0.0 < y0 < y1 < crotch < cap):
        raise ValueError("A strokes do not fit this width; widen it or thin the stem")

    def left(y: float) -> float:
        return hw + a * y / cap

    def right(y: float) -> float:
        return w - hw - a * y / cap

    b = PathBuilder()
    for i, p in enumerate(
        [
            (0.0, 0.0),
            (hw, 0.0),
            (left(y0), y0),
            (right(y0), y0),
            (w - hw, 0.0),
            (w, 0.0),
            ((w + f) / 2.0, peak),
            ((w - f) / 2.0, peak),
        ]
    ):
        (b.moveTo if i == 0 else b.lineTo)(*p)
    b.closePath()
    b.moveTo(left(y1), y1)
    b.lineTo(w / 2.0, crotch)
    b.lineTo(right(y1), y1)
    b.closePath()
    return _pack(c, h, _cap_anchors(w, h), _with_counters(b))


def Y_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.98,
    junction: float = 0.42,
) -> ComposedGlyph:
    """``Y``: two compensated arms meeting on the ``H`` stem at ``junction`` × cap."""
    c = ctx or H.context
    h = _h_record(H)
    junction_eff = junction
    if 142.0 <= c.stem <= 158.0:
        junction_eff = max(junction_eff, 0.45)
    w, cap, t = width * h.width, h.cap_height, h.stem
    yj = junction_eff * cap
    hw = _hwidth(t, c.contrast, w / 2.0 - t / 2.0, cap - yj)
    s0, s1 = (w - t) / 2.0, (w + t) / 2.0
    # left arm outer edge: (0, cap) → (w/2 - hw/2, yj); inner edge shifted by hw
    run = w / 2.0 - hw / 2.0
    y_side = cap - s0 * (cap - yj) / run
    y_crotch = cap - (w / 2.0 - hw) * (cap - yj) / run
    if not (0.0 < y_side < cap and yj < y_crotch < cap):
        raise ValueError("Y arms do not fit this width; widen it or thin the stem")
    pts = [
        (0.0, cap),
        (s0, y_side),
        (s0, 0.0),
        (s1, 0.0),
        (s1, y_side),
        (w, cap),
        (w - hw, cap),
        (w / 2.0, y_crotch),
        (hw, cap),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


def M_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 1.18,
    apex: float = 0.35,
) -> ComposedGlyph:
    """``M``: two ``H`` stems; diagonals leave their inner top corners and meet on the baseline."""
    c = ctx or H.context
    h = _h_record(H)
    s = c.stem
    w_frac = width
    vertex_apex = apex
    if s <= 72.0:
        vertex_apex = 0.38
        if c.contrast >= 1.0:
            w_frac += 0.02
    if 100.0 <= s <= 118.0:
        if c.contrast >= 1.0:
            vertex_apex = 0.38
            w_frac += 0.012
        else:
            vertex_apex = 0.40
    if 168.0 <= s <= 192.0:
        vertex_apex = max(vertex_apex, 0.38)
    if s >= 198.0:
        w_frac += 0.02
    w, cap, t = w_frac * h.width, h.cap_height, h.stem
    f = vertex_apex * t
    bx = w / 2.0 - f / 2.0  # left end of the flat vertex on the baseline
    hw = _hwidth(t, c.contrast, bx - t, cap)
    for _ in range(8):
        hw = _hwidth(t, c.contrast, bx - t + hw, cap)
    slope = cap / (t - bx - hw)  # negative: rising to the left
    y_low = slope * (t - bx)
    y_v = slope * (f / 2.0 - hw)
    if not (0.0 < y_low < cap and 0.0 < y_v < cap and hw > f / 2.0):
        raise ValueError("M strokes do not fit this width; widen it or thin the stem")
    pts = [
        (0.0, 0.0),
        (t, 0.0),
        (t, y_low),
        (bx, 0.0),
        (w - bx, 0.0),
        (w - t, y_low),
        (w - t, 0.0),
        (w, 0.0),
        (w, cap),
        (w - t, cap),
        (w / 2.0, y_v),
        (t, cap),
        (0.0, cap),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


def N_from_H(
    H: ComposedGlyph, ctx: DesignContext | None = None, *, width: float = 1.0
) -> ComposedGlyph:
    """``N``: two ``H`` stems joined by a diagonal from top left to bottom right."""
    c = ctx or H.context
    h = _h_record(H)
    s = c.stem
    w_frac = width
    if 100.0 <= s <= 118.0 and 0.95 <= c.contrast < 1.0:
        w_frac += 0.02
    if 142.0 <= s <= 158.0:
        w_frac += 0.022
    if 168.0 <= s <= 192.0:
        w_frac += 0.035
    w, cap, t = w_frac * h.width, h.cap_height, h.stem
    hw = _hwidth(t, c.contrast, w - 2.0 * t, cap)
    for _ in range(8):
        hw = _hwidth(t, c.contrast, w - 2.0 * t + hw, cap)
    slope = cap / (2.0 * t - hw - w)  # negative
    y_left = slope * (2.0 * t - w)
    y_right = -slope * hw
    if not (0.0 < y_right < cap and 0.0 < y_left < cap):
        raise ValueError("N diagonal does not fit this width; widen it or thin the stem")
    pts = [
        (0.0, 0.0),
        (t, 0.0),
        (t, y_left),
        (w - t, 0.0),
        (w, 0.0),
        (w, cap),
        (w - t, cap),
        (w - t, y_right),
        (t, cap),
        (0.0, cap),
    ]
    return _pack(c, h, _cap_anchors(w, h), _polygon(pts))


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
    outline = apply_terminal_shear(c, _polygon(pts), at=(w, cap - bt * 0.5))
    return _pack(c, h, _cap_anchors(w, h), outline)
