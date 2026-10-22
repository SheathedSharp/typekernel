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
from typing import Any, Literal

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
    _apply_italic_opening_tip_shear,
    _ccw,
    _curve,
    _cut,
    _emit_italic_entry_kick,
    _emit_italic_exit_outstroke,
    _italic_kick_dims,
    _italic_single_stem_outline,
    _italic_topology,
    _opening_slab_metrics,
    _opening_top_bracketed_move,
    _opening_top_slab_move,
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
from typekernel.parts.diagonals import (
    _crotch_seal_flat,
    _hwidth,
    _soft_corner_polygon,
    _truncate_crotch,
    k_points,
    v_points,
    w_points,
    x_points,
    z_points,
)
from typekernel.parts.terminal_openings import apply_terminal_shear, opening_closure
from typekernel.parts.weight_relief import min_bowl_stems

__all__ = [
    "A_from_H",
    "A_yoke",
    "B_from_H",
    "B_yoke",
    "build_H",
    "build_O",
    "C_from_O",
    "C_yoke",
    "cap_o_metrics",
    "D_from_H",
    "D_yoke",
    "E_from_H",
    "E_yoke",
    "F_from_H",
    "F_yoke",
    "G_from_O",
    "G_yoke",
    "h_cap_metrics",
    "H_yoke",
    "HMetrics",
    "I_from_H",
    "I_yoke",
    "J_from_H",
    "J_yoke",
    "K_from_H",
    "K_yoke",
    "L_from_H",
    "L_yoke",
    "M_from_H",
    "M_yoke",
    "N_from_H",
    "N_yoke",
    "O_yoke",
    "P_from_H",
    "P_yoke",
    "Q_from_O",
    "Q_yoke",
    "R_from_H",
    "R_yoke",
    "S_from_O",
    "S_yoke",
    "T_from_H",
    "T_yoke",
    "U_from_H",
    "U_yoke",
    "V_from_H",
    "V_yoke",
    "W_from_H",
    "W_yoke",
    "X_from_H",
    "X_yoke",
    "Y_from_H",
    "Y_yoke",
    "Z_from_H",
    "Z_yoke",
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


StemSerifMode = Literal["dual", "left", "none"]


def _cap_stem_serif_mode(span_width: float, h: HMetrics) -> StemSerifMode:
    """Pick stem serif sites from glyph span vs the control ``H`` width."""
    if abs(span_width - h.width) < 0.5:
        return "dual"
    if span_width > h.width + h.stem * 0.25:
        return "none"
    if span_width < h.width - 0.5:
        return "left"
    return "none"


def _cap_stem_serif_anchors(h: HMetrics, *, mode: StemSerifMode) -> dict[str, Pt]:
    half = h.stem / 2.0
    if mode == "none":
        return {}
    anchors: dict[str, Pt] = {
        "stem_L_b": (half, 0.0),
        "stem_L_t": (half, h.cap_height),
    }
    if mode == "dual":
        anchors["stem_R_b"] = (h.width - half, 0.0)
        anchors["stem_R_t"] = (h.width - half, h.cap_height)
    return anchors


def _cap_anchors(
    width: float,
    h: HMetrics,
    *,
    stem_serif_anchors: bool = True,
    stem_serif_mode: StemSerifMode | None = None,
) -> dict[str, Pt]:
    anchors: dict[str, Pt] = {
        "top": (width / 2.0, h.cap_height),
        "bottom": (width / 2.0, 0.0),
    }
    if stem_serif_anchors:
        mode = stem_serif_mode if stem_serif_mode is not None else _cap_stem_serif_mode(width, h)
        anchors.update(_cap_stem_serif_anchors(h, mode=mode))
    return anchors


def _cap_serif_inlined(c: DesignContext) -> bool:
    """Serif feet baked into the outline (slab rectangles; bracketed cubic where implemented)."""
    return c.style.serif in ("slab", "bracketed")


def _cap_italic_sans(c: DesignContext) -> bool:
    """Written italic foot craft on sans capitals (serif feet keep their own path)."""
    return _italic_topology(c) and not _cap_serif_inlined(c)


def _h_italic_sans_outline(h: HMetrics, ctx: DesignContext) -> Outline:
    """``H`` with shared lowercase entry kick + right-stem exit outstroke."""
    t, w, cap = h.stem, h.width, h.cap_height
    y0, y1 = h.bar_y - h.bar / 2.0, h.bar_y + h.bar / 2.0
    dx, _dy = _italic_kick_dims(t)
    b = PathBuilder()
    _emit_italic_entry_kick(b, 0.0, stem=t, left_top=cap)
    b.lineTo(t, cap)
    b.lineTo(t, y1)
    b.lineTo(w - t, y1)
    b.lineTo(w - t, cap)
    b.lineTo(w, cap)
    _emit_italic_exit_outstroke(b, w - t, w, stem=t)
    b.lineTo(w - t, y0)
    b.lineTo(t, y0)
    b.lineTo(t, 0.0)
    b.lineTo(dx, 0.0)
    b.closePath()
    return _ccw(b.build())


def _l_italic_sans_outline(h: HMetrics, ctx: DesignContext, *, width: float) -> Outline:
    """``L``: entry kick on the stem."""
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    dx, _dy = _italic_kick_dims(t)
    b = PathBuilder()
    _emit_italic_entry_kick(b, 0.0, stem=t, left_top=cap)
    b.lineTo(t, cap)
    b.lineTo(t, bt)
    b.lineTo(w, bt)
    b.lineTo(w, 0.0)
    b.lineTo(dx, 0.0)
    b.closePath()
    return _ccw(b.build())


def _e_italic_sans_outline(h: HMetrics, ctx: DesignContext, *, width: float) -> Outline:
    """``E``: entry kick on the stem."""
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid, w_bot = w * 0.97, w * 0.88, w
    m0, m1 = h.bar_y - bt / 2.0, h.bar_y + bt / 2.0
    dx, _dy = _italic_kick_dims(t)
    b = PathBuilder()
    _emit_italic_entry_kick(b, 0.0, stem=t, left_top=cap)
    b.lineTo(w_top, cap)
    b.lineTo(w_top, cap - bt)
    b.lineTo(t, cap - bt)
    b.lineTo(t, m1)
    b.lineTo(w_mid, m1)
    b.lineTo(w_mid, m0)
    b.lineTo(t, m0)
    b.lineTo(t, bt)
    b.lineTo(w_bot, bt)
    b.lineTo(w_bot, 0.0)
    b.lineTo(dx, 0.0)
    b.closePath()
    return _ccw(b.build())


def _f_italic_sans_outline(h: HMetrics, ctx: DesignContext, *, width: float) -> Outline:
    """``F``: entry kick + stem-foot exit outstroke."""
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid = w, w * 0.9
    mid = h.bar_y - 0.03 * cap
    m0, m1 = mid - bt / 2.0, mid + bt / 2.0
    dx, _dy = _italic_kick_dims(t)
    b = PathBuilder()
    _emit_italic_entry_kick(b, 0.0, stem=t, left_top=cap)
    b.lineTo(w_top, cap)
    b.lineTo(w_top, cap - bt)
    b.lineTo(t, cap - bt)
    b.lineTo(t, m1)
    b.lineTo(w_mid, m1)
    b.lineTo(w_mid, m0)
    b.lineTo(t, m0)
    _emit_italic_exit_outstroke(b, 0.0, t, stem=t)
    b.lineTo(dx, 0.0)
    b.closePath()
    return _ccw(b.build())




def _n_italic_sans_outline(
    h: HMetrics,
    ctx: DesignContext,
    *,
    w: float,
    y_left: float,
    y_right: float,
) -> Outline:
    """``N``: entry kick + right-stem exit outstroke (sans)."""
    t, cap = h.stem, h.cap_height
    dx, _dy = _italic_kick_dims(t)
    b = PathBuilder()
    _emit_italic_entry_kick(b, 0.0, stem=t, left_top=cap)
    b.lineTo(t, cap)
    b.lineTo(w - t, y_right)
    b.lineTo(w - t, cap)
    b.lineTo(w, cap)
    _emit_italic_exit_outstroke(b, w - t, w, stem=t)
    b.lineTo(t, y_left)
    b.lineTo(t, 0.0)
    b.lineTo(dx, 0.0)
    b.closePath()
    return _ccw(b.build())


def _m_italic_sans_outline(
    h: HMetrics,
    ctx: DesignContext,
    *,
    w: float,
    y_low: float,
    y_v: float,
    bx: float,
) -> Outline:
    """``M``: entry kick + right-stem exit outstroke (sans)."""
    t, cap = h.stem, h.cap_height
    dx, _dy = _italic_kick_dims(t)
    b = PathBuilder()
    _emit_italic_entry_kick(b, 0.0, stem=t, left_top=cap)
    b.lineTo(t, cap)
    b.lineTo(w / 2.0, y_v)
    b.lineTo(w - t, cap)
    b.lineTo(w, cap)
    _emit_italic_exit_outstroke(b, w - t, w, stem=t)
    b.lineTo(w - t, y_low)
    b.lineTo(w - bx, 0.0)
    b.lineTo(bx, 0.0)
    b.lineTo(t, y_low)
    b.lineTo(t, 0.0)
    b.lineTo(dx, 0.0)
    b.closePath()
    return _ccw(b.build())


def _t_italic_sans_outline(h: HMetrics, ctx: DesignContext, *, width: float) -> Outline:
    """``T``: stem entry kick + foot outstroke; bar tips sheared by caller."""
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    s0, s1 = (w - t) / 2.0, (w + t) / 2.0
    dx, _dy = _italic_kick_dims(t)
    b = PathBuilder()
    _emit_italic_entry_kick(b, s0, stem=t, left_top=cap - bt)
    b.lineTo(0.0, cap - bt)
    b.lineTo(0.0, cap)
    b.lineTo(w, cap)
    b.lineTo(w, cap - bt)
    b.lineTo(s1, cap - bt)
    _emit_italic_exit_outstroke(b, s0, s1, stem=t)
    b.lineTo(s0 + dx, 0.0)
    b.closePath()
    return _ccw(b.build())

def _cap_stem_serif_anchors_enabled(
    c: DesignContext, *, baked: bool, diagonal: bool = False
) -> bool:
    """Whether cap stem sites get boolean serifs (slab inline and diagonals opt out)."""
    return not (baked or diagonal)


def _h_cap_foot_dims(h: HMetrics, ctx: DesignContext) -> tuple[float, float, float]:
    t, w = h.stem, h.width
    y0 = h.bar_y - h.bar / 2.0
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    gap = max(w - 2.0 * t, t)
    l = min(length, t * 0.48, gap * 0.32)
    th = min(thick, y0 * 0.36, t * 0.18, gap * 0.14)
    return l, th, bracket_r


def _write_h_bracketed_outer(b: PathBuilder, h: HMetrics, ctx: DesignContext) -> None:
    """Bracketed ``H``: dual-stem inline serifs with cubic fillets (VF-stable)."""
    t, w, cap = h.stem, h.width, h.cap_height
    y0, y1 = h.bar_y - h.bar / 2.0, h.bar_y + h.bar / 2.0
    l, th, bracket_r = _h_cap_foot_dims(h, ctx)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    b.lineTo(t, 0.0)
    b.lineTo(t, y0)
    b.lineTo(w - t, y0)
    b.lineTo(w - t, 0.0)
    b.lineTo(w - t - l, -th)
    _finish_baseline_foot_pad(b, w - t - l, w + l, th, bracket_r, bracketed=True)
    b.lineTo(w, 0.0)
    b.lineTo(w, cap)
    b.lineTo(w + l, cap)
    _append_upward_cap_foot_pad(b, w - t - l, w + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(w - t, cap)
    b.lineTo(w - t, y1)
    b.lineTo(t, y1)
    b.lineTo(t, cap)
    b.lineTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()


def _h_outline_points(h: HMetrics, ctx: DesignContext) -> list[Pt]:
    """Single CCW outer for ``H``; bakes slab serifs when ``style.serif`` is set."""
    t, w, cap = h.stem, h.width, h.cap_height
    y0, y1 = h.bar_y - h.bar / 2.0, h.bar_y + h.bar / 2.0
    if ctx.style.serif != "slab":
        return [
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
    l, th, _ = _h_cap_foot_dims(h, ctx)
    return [
        (-l, -th),
        (t + l, -th),
        (t + l, 0.0),
        (t, 0.0),
        (t, y0),
        (w - t, y0),
        (w - t, 0.0),
        (w - t - l, 0.0),
        (w - t - l, -th),
        (w + l, -th),
        (w + l, 0.0),
        (w, 0.0),
        (w, cap),
        (w + l, cap),
        (w + l, cap + th),
        (w - t - l, cap + th),
        (w - t - l, cap),
        (w - t, cap),
        (w - t, y1),
        (t, y1),
        (t, cap),
        (t + l, cap),
        (t + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def _i_slab_outline_points(h: HMetrics, ctx: DesignContext) -> list[Pt]:
    t, cap = h.stem, h.cap_height
    from typekernel.parts.serifs import serif_metrics

    length, thick, _ = serif_metrics(ctx)
    l = min(length, t * 0.5)
    th = min(thick, cap * 0.1, t * 0.2)
    return [
        (-l, -th),
        (t + l, -th),
        (t + l, 0.0),
        (t, 0.0),
        (t, cap),
        (t + l, cap),
        (t + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def H_yoke(ctx: DesignContext, *, metrics: HMetrics | None = None) -> Outline:
    """Continuous ``H`` body — Usage A (two stems + crossbar, one contour).

    Matches :func:`build_H` across sans / slab / bracketed / italic sans.
    """
    h = metrics or h_cap_metrics(ctx)
    if ctx.style.serif == "bracketed":
        b = PathBuilder()
        _write_h_bracketed_outer(b, h, ctx)
        return _ccw(b.build())
    if _cap_italic_sans(ctx):
        return _h_italic_sans_outline(h, ctx)
    return _polygon(_h_outline_points(h, ctx))


def build_H(ctx: DesignContext, metrics: HMetrics | None = None) -> ComposedGlyph:
    """Control ``H``: two cap stems and a crossbar, one contour."""
    h = metrics or h_cap_metrics(ctx)
    baked = ctx.style.serif == "slab"
    outline = H_yoke(ctx, metrics=h)
    serif_anchors = not (baked or ctx.style.serif == "bracketed" or _cap_italic_sans(ctx))
    return _pack(
        ctx,
        h,
        _cap_anchors(h.width, h, stem_serif_anchors=serif_anchors),
        outline,
    )


def O_yoke(ctx: DesignContext, *, metrics: OMetrics | None = None) -> Outline:
    """Continuous cap ``O`` body (outer + counter) — Usage A.

    Cap-height ring with the cap stem; ink-local (no sidebearings), same
    recipe as :func:`build_O` / lowercase :func:`~typekernel.parts.control.o_yoke`.
    """
    from typekernel.geo.contour import reverse_contour
    from typekernel.parts.primitives import bowl

    m = metrics or cap_o_metrics(ctx)
    cx, cy = m.rx, m.x_height / 2.0
    outer, hole = bowl(
        ctx,
        cx,
        cy,
        rx=m.rx,
        ry=m.ry,
        thickness_v=m.thickness_v,
        thickness_h=m.thickness_h,
        shape="superellipse",
        n=m.exponent,
    )
    return Outline((outer.contours[0], reverse_contour(hole.contours[0])))


def build_O(ctx: DesignContext, metrics: OMetrics | None = None) -> ComposedGlyph:
    """Control ``O``: the ``o`` ring drawn at cap height with the cap stem."""
    m = metrics or cap_o_metrics(ctx)
    return build_o(ctx, m)


def _i_cap_foot_dims(h: HMetrics, ctx: DesignContext) -> tuple[float, float, float]:
    return _k_cap_foot_dims(h, ctx)


def _write_i_bracketed_outer(b: PathBuilder, h: HMetrics, ctx: DesignContext) -> None:
    t, cap = h.stem, h.cap_height
    l, th, bracket_r = _i_cap_foot_dims(h, ctx)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    b.lineTo(t, 0.0)
    b.lineTo(t, cap)
    b.lineTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()


def I_yoke(ctx: DesignContext, *, metrics: HMetrics | None = None) -> Outline:
    """Continuous cap ``I`` stem body — Usage A.

    Matches :func:`I_from_H` (slab / bracketed / italic / soft-corner sans).
    """
    h = metrics or h_cap_metrics(ctx)
    cap = h.cap_height
    if ctx.style.serif == "slab":
        return _polygon(_i_slab_outline_points(h, ctx))
    if ctx.style.serif == "bracketed":
        b = PathBuilder()
        _write_i_bracketed_outer(b, h, ctx)
        return _ccw(b.build())
    if _cap_italic_sans(ctx):
        return _italic_single_stem_outline(ctx, stem=h.stem, top=cap)
    from typekernel.parts.primitives import rounded_rect

    radius = min(ctx.join_radius * 0.4, h.stem * 0.16)
    r = max(radius, 1.0)
    if abs(ctx.contrast - 1.0) < 1e-9:
        return rounded_rect(ctx, 0.0, 0.0, h.stem, cap, radius=r)
    inset = (h.stem - h.stem * ctx.contrast) / 2.0
    x0, x1 = 0.0, h.stem
    xt0, xt1 = inset, h.stem - inset
    r = min(r, (x1 - x0) * 0.45, (xt1 - xt0) * 0.45, cap * 0.45)
    b = PathBuilder()
    b.moveTo(x0 + r, 0.0)
    b.lineTo(x1 - r, 0.0)
    b.curveTo(x1 - r + r * KAPPA, 0.0, x1, r - r * KAPPA, x1, r)
    b.lineTo(xt1, cap - r)
    b.curveTo(xt1, cap - r + r * KAPPA, xt1 - r + r * KAPPA, cap, xt1 - r, cap)
    b.lineTo(xt0 + r, cap)
    b.curveTo(xt0 + r - r * KAPPA, cap, xt0, cap - r + r * KAPPA, xt0, cap - r)
    b.lineTo(x0, r)
    b.curveTo(x0, r - r * KAPPA, x0 + r - r * KAPPA, 0.0, x0 + r, 0.0)
    b.closePath()
    return b.build()


def I_from_H(H: ComposedGlyph, ctx: DesignContext | None = None) -> ComposedGlyph:
    """``I``: one ``H`` stem."""
    c = ctx or H.context
    h = _h_record(H)
    half = h.stem / 2.0
    cap = h.cap_height
    outline = I_yoke(c, metrics=h)
    if c.style.serif in ("slab", "bracketed"):
        anchors = {"top": (half, cap), "bottom": (half, 0.0)}
    else:
        anchors = {
            **_cap_anchors(h.stem, h),
            "stem_L_b": (half, 0.0),
            "stem_L_t": (half, cap),
        }
    return _pack(c, h, anchors, outline)


def _l_cap_foot_dims(h: HMetrics, ctx: DesignContext) -> tuple[float, float, float]:
    t, cap, bt = h.stem, h.cap_height, h.bar
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    l = min(length, t * 0.5)
    th = min(thick, cap * 0.1, t * 0.2, bt * 0.45)
    return l, th, bracket_r


def _write_l_bracketed_outer(
    b: PathBuilder, h: HMetrics, ctx: DesignContext, *, width: float
) -> None:
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    l, th, bracket_r = _l_cap_foot_dims(h, ctx)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    b.lineTo(w, 0.0)
    b.lineTo(w, bt)
    b.lineTo(t, bt)
    b.lineTo(t, cap)
    b.lineTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()


def _l_outline_points(h: HMetrics, ctx: DesignContext, *, width: float) -> list[Pt]:
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    if ctx.style.serif != "slab":
        return [(0.0, 0.0), (w, 0.0), (w, bt), (t, bt), (t, cap), (0.0, cap)]
    l, th, _ = _l_cap_foot_dims(h, ctx)
    return [
        (-l, -th),
        (t + l, -th),
        (t + l, 0.0),
        (w, 0.0),
        (w, bt),
        (t, bt),
        (t, cap),
        (t + l, cap),
        (t + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def L_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.78,
) -> Outline:
    """Continuous cap ``L`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    if ctx.style.serif == "bracketed":
        b = PathBuilder()
        _write_l_bracketed_outer(b, h, ctx, width=width)
        return _ccw(b.build())
    if _cap_italic_sans(ctx):
        outline = _l_italic_sans_outline(h, ctx, width=width)
        return _apply_italic_opening_tip_shear(
            ctx, outline, ((width * h.width, h.bar * 0.5),), stem=h.stem
        )
    return _polygon(_l_outline_points(h, ctx, width=width))


def L_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.78,
) -> ComposedGlyph:
    """``L``: the ``H`` stem with a foot ``width`` × the ``H`` width."""
    c = ctx or H.context
    h = _h_record(H)
    w = width * h.width
    inlined = c.style.serif in ("slab", "bracketed")
    anchors = _cap_anchors(
        w, h, stem_serif_anchors=not inlined, stem_serif_mode="left"
    )
    return _pack(c, h, anchors, L_yoke(c, metrics=h, width=width))


def _e_outline_points(h: HMetrics, ctx: DesignContext, *, width: float) -> list[Pt]:
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid, w_bot = w * 0.97, w * 0.88, w
    m0, m1 = h.bar_y - bt / 2.0, h.bar_y + bt / 2.0
    if ctx.style.serif != "slab":
        return [
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
    l, th, _ = _l_cap_foot_dims(h, ctx)
    return [
        (-l, -th),
        (t + l, -th),
        (t + l, 0.0),
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
        (t + l, cap),
        (t + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def _write_e_bracketed_outer(
    b: PathBuilder, h: HMetrics, ctx: DesignContext, *, width: float
) -> None:
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid, w_bot = w * 0.97, w * 0.88, w
    m0, m1 = h.bar_y - bt / 2.0, h.bar_y + bt / 2.0
    l, th, bracket_r = _l_cap_foot_dims(h, ctx)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    b.lineTo(w_bot, 0.0)
    b.lineTo(w_bot, bt)
    b.lineTo(t, bt)
    b.lineTo(t, m0)
    b.lineTo(w_mid, m0)
    b.lineTo(w_mid, m1)
    b.lineTo(t, m1)
    b.lineTo(t, cap - bt)
    b.lineTo(w_top, cap - bt)
    b.lineTo(w_top, cap)
    b.lineTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()


def E_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.84,
) -> Outline:
    """Continuous cap ``E`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    if ctx.style.serif == "bracketed":
        b = PathBuilder()
        _write_e_bracketed_outer(b, h, ctx, width=width)
        return _ccw(b.build())
    if _cap_italic_sans(ctx):
        outline = _e_italic_sans_outline(h, ctx, width=width)
        w = width * h.width
        tips = (
            (w * 0.97, h.cap_height - h.bar * 0.5),
            (w * 0.88, h.bar_y),
            (w, h.bar * 0.5),
        )
        return _apply_italic_opening_tip_shear(ctx, outline, tips, stem=h.stem)
    return _polygon(_e_outline_points(h, ctx, width=width))


def E_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.84,
) -> ComposedGlyph:
    """``E``: stem with three arms; the middle arm is shorter, the foot longest."""
    c = ctx or H.context
    h = _h_record(H)
    w = width * h.width
    inlined = c.style.serif in ("slab", "bracketed")
    anchors = _cap_anchors(
        w, h, stem_serif_anchors=not inlined, stem_serif_mode="left"
    )
    return _pack(c, h, anchors, E_yoke(c, metrics=h, width=width))


def _f_outline_points(h: HMetrics, ctx: DesignContext, *, width: float) -> list[Pt]:
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid = w, w * 0.9
    mid = h.bar_y - 0.03 * cap
    m0, m1 = mid - bt / 2.0, mid + bt / 2.0
    if ctx.style.serif != "slab":
        return [
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
    l, th, _ = _l_cap_foot_dims(h, ctx)
    return [
        (-l, -th),
        (t + l, -th),
        (t + l, 0.0),
        (t, 0.0),
        (t, m0),
        (w_mid, m0),
        (w_mid, m1),
        (t, m1),
        (t, cap - bt),
        (w_top, cap - bt),
        (w_top, cap),
        (t + l, cap),
        (t + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def _write_f_bracketed_outer(
    b: PathBuilder, h: HMetrics, ctx: DesignContext, *, width: float
) -> None:
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    w_top, w_mid = w, w * 0.9
    mid = h.bar_y - 0.03 * cap
    m0, m1 = mid - bt / 2.0, mid + bt / 2.0
    l, th, bracket_r = _l_cap_foot_dims(h, ctx)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    b.lineTo(t, 0.0)
    b.lineTo(t, m0)
    b.lineTo(w_mid, m0)
    b.lineTo(w_mid, m1)
    b.lineTo(t, m1)
    b.lineTo(t, cap - bt)
    b.lineTo(w_top, cap - bt)
    b.lineTo(w_top, cap)
    b.lineTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()


def F_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.82,
    real_flare: bool = False,
) -> Outline:
    """Continuous cap ``F`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    w = width * h.width
    w_top = w
    if ctx.style.serif == "bracketed":
        b = PathBuilder()
        _write_f_bracketed_outer(b, h, ctx, width=width)
        return _ccw(b.build())
    if _cap_italic_sans(ctx):
        outline = _f_italic_sans_outline(h, ctx, width=width)
        return _apply_italic_opening_tip_shear(
            ctx,
            outline,
            ((w_top, h.cap_height - h.bar * 0.5), (w_top * 0.9, h.bar_y)),
            stem=h.stem,
        )
    pts = _f_outline_points(h, ctx, width=width)
    if ctx.style.serif == "slab":
        return _polygon(pts)
    return _cap_f_t_outline(
        ctx, pts, w_top, h.cap_height, h.bar, real_flare=real_flare
    )


def F_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.82,
    real_flare: bool = False,
) -> ComposedGlyph:
    """``F``: the ``E`` without its foot; the middle arm sits a little lower."""
    c = ctx or H.context
    h = _h_record(H)
    w = width * h.width
    inlined = c.style.serif in ("slab", "bracketed")
    anchors = _cap_anchors(
        w, h, stem_serif_anchors=not inlined, stem_serif_mode="left"
    )
    return _pack(
        c, h, anchors, F_yoke(c, metrics=h, width=width, real_flare=real_flare)
    )


def _cap_f_t_outline(
    c: DesignContext,
    pts: list[tuple[float, float]],
    w_top: float,
    cap: float,
    bt: float,
    *,
    real_flare: bool = False,
) -> Outline:
    tip = (w_top, cap - bt * 0.5)
    poly = _polygon(pts)
    if real_flare:
        return apply_terminal_shear(
            c, poly, at=tip, along="x", inward="-", real_flare=True
        )
    if c.terminal_style == "vertical":
        return poly
    if c.terminal_style == "horizontal":
        return apply_terminal_shear(c, poly, at=tip, prefer_flat=True)
    if c.terminal_style == "angled":
        return apply_terminal_shear(c, poly, at=tip, along="x", inward="-")
    if c.terminal_style == "flared":
        return apply_terminal_shear(c, poly, at=tip, along="x", inward="-")
    return apply_terminal_shear(c, poly, at=tip)


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


def C_yoke(
    ctx: DesignContext,
    *,
    aperture: float | None = None,
    metrics: OMetrics | None = None,
) -> Outline:
    """Continuous cap ``C`` body — Usage A (opening on the cap ``O``).

    Ink-local outline; reuses the lowercase ``c`` opening recipe at cap metrics.
    """
    from typekernel.parts.control import _c_opening_outline

    o = metrics or cap_o_metrics(ctx)
    return _c_opening_outline(ctx, o, aperture=aperture)


def S_yoke(
    ctx: DesignContext,
    *,
    width: float = 0.86,
    aperture: float | None = None,
    metrics: OMetrics | None = None,
) -> Outline:
    """Continuous cap ``S`` body — Usage A (spine on the cap ``O``)."""
    from typekernel.parts.control import _s_opening_outline

    o = metrics or cap_o_metrics(ctx)
    outline, _tips = _s_opening_outline(
        ctx, o, aperture=aperture, width=width
    )
    return outline


def S_from_O(
    O: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.86,
) -> ComposedGlyph:
    """``S``: the lowercase ``s`` construction on the cap ``O``, a little wider."""
    return s_from_o(O, ctx, width=width)


def G_yoke(
    ctx: DesignContext,
    *,
    metrics: OMetrics | None = None,
    h_metrics: HMetrics | None = None,
    bar_reach: float = 0.1,
) -> Outline:
    """Continuous cap ``G`` body — Usage A (``C`` + inward crossbar)."""
    o = metrics or cap_o_metrics(ctx)
    h = h_metrics or h_cap_metrics(ctx)
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o, ctx)
    cx, cy = o.rx, o.x_height / 2.0
    x_t = _terminal_x(o, ctx.aperture, opening_closure(ctx, 0.55))
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
    inlined = _cap_serif_inlined(ctx)
    if ctx.style.serif == "bracketed":
        slab_l, slab_th = _opening_slab_metrics(ctx, o)
        from typekernel.parts.serifs import serif_metrics

        _, _, bracket_r = serif_metrics(ctx)
        _opening_top_bracketed_move(b, top[0], slab_l, slab_th, bracket_r)
    elif inlined:
        slab_l, slab_th = _opening_slab_metrics(ctx, o)
        _opening_top_slab_move(b, top[0], slab_l, slab_th)
    else:
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
    outline = _ccw(b.build())
    if _cap_italic_sans(ctx):
        tips = (
            top[0],
            (x_bar, (bar_top + bar_bot) * 0.5),
        )
        outline = _apply_italic_opening_tip_shear(
            ctx, outline, tips, stem=o.thickness_v
        )
    return outline


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
    inlined = _cap_serif_inlined(c)
    outline = G_yoke(c, metrics=o, h_metrics=h, bar_reach=bar_reach)
    return _pack(
        c,
        o,
        _cap_anchors(2.0 * o.rx, h, stem_serif_anchors=not inlined),
        outline,
    )


def Q_yoke(
    ctx: DesignContext,
    *,
    metrics: OMetrics | None = None,
    h_metrics: HMetrics | None = None,
    tail_reach: float = 1.0,
    tail_drop: float = 0.1,
) -> Outline:
    """Continuous cap ``Q`` body — Usage A (``O`` + spliced diagonal tail)."""
    o = metrics or cap_o_metrics(ctx)
    h = h_metrics or h_cap_metrics(ctx)
    (q0, q1, q2, q3), (i0, i1, i2, i3) = _ring(o, ctx)
    cx, cy = o.rx, o.x_height / 2.0
    k = math.cos(math.radians(45.0))
    start_pt = (
        cx + (o.rx - o.thickness_v / 2.0) * k,
        cy - (o.ry - o.thickness_h / 2.0) * k,
    )
    end = (cx + tail_reach * o.rx, -o.overshoot - tail_drop * o.x_height)
    hw = _hwidth(h.stem * 0.95, ctx.contrast, end[0] - start_pt[0], start_pt[1] - end[1])
    hits: list[float] = []
    for side in (-0.5, 0.5):
        a = (start_pt[0] + side * hw, start_pt[1])
        z = (end[0] + side * hw, end[1])
        far = (a[0] - (z[0] - a[0]), a[1] - (z[1] - a[1]))
        found = [
            i.t1
            for i in curveLineIntersections(list(q3), [far, z])
            if 0.0 < i.t1 < 1.0
        ]
        if len(found) != 1:
            raise ValueError("Q tail does not meet the bowl once per edge; adjust the O")
        hits.append(found[0])
    t_lo, t_hi = sorted(hits)
    before, _, after = splitCubicAtT(*q3, t_lo, t_hi)

    b = PathBuilder()
    b.moveTo(*q0[0])
    for cubic in (q0, q1, q2, before):
        _curve(b, cubic)
    inlined = _cap_serif_inlined(ctx)
    tail_l = end[0] - hw / 2.0
    tail_r = end[0] + hw / 2.0
    tail_y = end[1]
    if ctx.style.serif == "bracketed" or inlined:
        from typekernel.parts.serifs import serif_metrics

        length, thick, bracket_r = serif_metrics(ctx)
        cap = o.x_height
        foot_l = min(length * 0.35, hw * 0.55, h.stem * 0.28)
        foot_th = min(thick * 0.55, cap * 0.04, h.stem * 0.1)
        b.lineTo(tail_l, tail_y)
        b.lineTo(tail_l - foot_l, tail_y)
        if ctx.style.serif == "bracketed":
            _finish_foot_pad_below(
                b,
                tail_l - foot_l,
                tail_r + foot_l,
                tail_y,
                foot_th,
                bracket_r,
                bracketed=True,
            )
        else:
            b.lineTo(tail_l - foot_l, tail_y - foot_th)
            b.lineTo(tail_r + foot_l, tail_y - foot_th)
            b.lineTo(tail_r + foot_l, tail_y)
        b.lineTo(tail_r, tail_y)
    else:
        b.lineTo(tail_l, tail_y)
        b.lineTo(tail_r, tail_y)
    b.lineTo(*after[0])
    _curve(b, after)
    b.closePath()
    b.moveTo(*i0[0])
    for cubic in (i0, i1, i2, i3):
        _curve(b, cubic)
    b.closePath()
    outer, counter = b.build().contours
    return Outline((outer, reverse_contour(counter)))


def Q_from_O(
    O: ComposedGlyph,
    H: ComposedGlyph | None = None,
    ctx: DesignContext | None = None,
    *,
    tail_reach: float = 1.0,
    tail_drop: float = 0.1,
) -> ComposedGlyph:
    """``Q``: the ``O`` with a compensated diagonal tail from its lower right.

    The tail's two edges are intersected with the bowl's lower-right outer
    quarter and spliced in, so the outer contour grows the tail and the
    counter stays the ``O``'s — no overlap, no boolean, fixed topology.

    ``tail_reach`` × ``O`` radius sets how far the tail tip sits to the right of
    centre; ``tail_drop`` × x-height sets depth below the baseline overshoot.
    """
    c = ctx or O.context
    o = _o_rec(O)
    h = _h_record(H) if H is not None else h_cap_metrics(c)
    inlined = _cap_serif_inlined(c)
    outline = Q_yoke(
        c, metrics=o, h_metrics=h, tail_reach=tail_reach, tail_drop=tail_drop
    )
    return _pack(
        c,
        o,
        _cap_anchors(2.0 * o.rx, h, stem_serif_anchors=not inlined),
        outline,
    )


def D_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
    width: float = 1.05,
    straight: float = 0.4,
) -> Outline:
    """Continuous cap ``D`` body — Usage A (stem + half bowl, outer + counter)."""
    h = metrics or h_cap_metrics(ctx)
    e = (o_metrics_rec or cap_o_metrics(ctx)).exponent
    st, cap, bt = h.stem, h.cap_height, h.bar
    w = max(width * h.width, min_bowl_stems(st) * st + 0.3 * st)
    x0 = _straight_run(straight, w, st)
    cy = cap / 2.0
    _, _, _, q3 = _quarters(x0, cy, w - x0, cy, e)
    q0 = _quarters(x0, cy, w - x0, cy, e)[0]
    _, _, _, i3 = _quarters(x0, cy, w - x0 - st, cy - bt, e)
    i0 = _quarters(x0, cy, w - x0 - st, cy - bt, e)[0]

    inlined = _cap_serif_inlined(ctx)
    b = PathBuilder()
    foot_l = 0.0
    if ctx.style.serif == "bracketed":
        foot_l = _bowl_cap_bracketed_foot_start(b, h, ctx, stem_x=x0)
    elif inlined:
        l, th, _ = _bowl_cap_stem_foot_dims(h, ctx)
        foot_l = l
        b.moveTo(-l, -th)
        b.lineTo(st + l, -th)
        b.lineTo(st + l, 0.0)
        b.lineTo(x0, 0.0)
    else:
        b.moveTo(0.0, 0.0)
        b.lineTo(x0, 0.0)
    _curve(b, q3)
    _curve(b, q0)
    if ctx.style.serif == "bracketed":
        _bowl_cap_bracketed_close_left(b, cap=cap, l=foot_l)
    elif inlined:
        b.lineTo(0.0, cap)
        b.lineTo(0.0, 0.0)
        b.lineTo(-foot_l, 0.0)
    else:
        b.lineTo(0.0, cap)
    b.closePath()
    b.moveTo(st, bt)
    b.lineTo(st, cap - bt)
    b.lineTo(x0, cap - bt)
    _curve(b, _rev(i0))
    _curve(b, _rev(i3))
    b.closePath()
    outer, counter = b.build().contours
    return _ccw(Outline((outer, counter)))


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
    o_rec = _o_rec(O) if O is not None else cap_o_metrics(c)
    st = h.stem
    w = max(width * h.width, min_bowl_stems(st) * st + 0.3 * st)
    inlined = _cap_serif_inlined(c)
    outline = D_yoke(
        c, metrics=h, o_metrics_rec=o_rec, width=width, straight=straight
    )
    return _pack(
        c,
        h,
        _cap_anchors(w, h, stem_serif_anchors=not inlined),
        outline,
    )


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


def _bowl_cap_stem_foot_dims(h: HMetrics, ctx: DesignContext) -> tuple[float, float, float]:
    t, cap = h.stem, h.cap_height
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    l = min(length, t * 0.48)
    th = min(thick, cap * 0.1, t * 0.18)
    return l, th, bracket_r


def _bowl_cap_bracketed_foot_start(
    b: PathBuilder, h: HMetrics, ctx: DesignContext, *, stem_x: float
) -> float:
    """Left stem baseline foot with cubic bracket; ends at ``(stem_x, 0)``."""
    t = h.stem
    l, th, bracket_r = _bowl_cap_stem_foot_dims(h, ctx)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    b.lineTo(stem_x, 0.0)
    return l


def _bowl_cap_bracketed_close_left(b: PathBuilder, *, cap: float, l: float) -> None:
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)


def P_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
    width: float = 0.9,
    straight: float = 0.45,
    bowl: float = 0.47,
) -> Outline:
    """Continuous cap ``P`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    e = (o_metrics_rec or cap_o_metrics(ctx)).exponent
    st, cap, bt = h.stem, h.cap_height, h.bar
    w = max(width * h.width, min_bowl_stems(st) * st)
    x0, y_b = _straight_run(straight, w, st), bowl * cap - bt / 2.0
    q3, q0, i3, i0 = _half_bowl(x0, y_b, cap, w, st, bt, e)
    inlined = _cap_serif_inlined(ctx)
    b = PathBuilder()
    foot_l = 0.0
    if ctx.style.serif == "bracketed":
        foot_l = _bowl_cap_bracketed_foot_start(b, h, ctx, stem_x=st)
    elif inlined:
        l, th, _ = _bowl_cap_stem_foot_dims(h, ctx)
        foot_l = l
        b.moveTo(-l, -th)
        b.lineTo(st + l, -th)
        b.lineTo(st + l, 0.0)
        b.lineTo(st, 0.0)
    else:
        b.moveTo(0.0, 0.0)
        b.lineTo(st, 0.0)
    for pt in ((st, y_b), (x0, y_b)):
        b.lineTo(*pt)
    _curve(b, q3)
    _curve(b, q0)
    if ctx.style.serif == "bracketed":
        _bowl_cap_bracketed_close_left(b, cap=cap, l=foot_l)
    elif inlined:
        b.lineTo(0.0, cap)
        b.lineTo(0.0, 0.0)
        b.lineTo(-foot_l, 0.0)
    else:
        b.lineTo(0.0, cap)
    b.closePath()
    _counter(b, st, x0, i3, i0)
    return _with_counters(b)


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
    st = h.stem
    w = max(width * h.width, min_bowl_stems(st) * st)
    inlined = _cap_serif_inlined(c)
    o_rec = _o_rec(O) if O is not None else cap_o_metrics(c)
    outline = P_yoke(
        c,
        metrics=h,
        o_metrics_rec=o_rec,
        width=width,
        straight=straight,
        bowl=bowl,
    )
    return _pack(
        c,
        h,
        _cap_anchors(w, h, stem_serif_anchors=not inlined, stem_serif_mode="left"),
        outline,
    )


def R_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
    width: float = 0.94,
    straight: float = 0.45,
    bowl: float = 0.47,
    leg_at: float = 0.3,
) -> Outline:
    """Continuous cap ``R`` body — Usage A (``P`` + compensated leg)."""
    h = metrics or h_cap_metrics(ctx)
    e = (o_metrics_rec or cap_o_metrics(ctx)).exponent
    st, cap, bt = h.stem, h.cap_height, h.bar
    w = max(width * h.width, min_bowl_stems(st) * st)
    bowl_w = 0.96 * w
    x0, y_b = _straight_run(straight, bowl_w, st), bowl * cap - bt / 2.0
    q3, q0, i3, i0 = _half_bowl(x0, y_b, cap, bowl_w, st, bt, e)
    foot_r = (w, 0.0)
    lo, hi, t_c = 0.0, 1.0, leg_at
    for _ in range(40):
        pc = cubicPointAtT(*q3, t_c)
        hw = _hwidth(h.stem * 0.95, ctx.contrast, w - pc[0], pc[1])
        x_l = (w - hw) + (pc[0] - w) * (y_b / pc[1])
        if x_l > x0:
            hi, t_c = t_c, (lo + t_c) / 2.0
        elif x_l < st:
            lo, t_c = t_c, (t_c + hi) / 2.0
        else:
            break
    else:
        raise ValueError("R leg does not fit between stem and bowl; adjust width")
    _, after = splitCubicAtT(*q3, t_c)

    inlined = _cap_serif_inlined(ctx)
    b = PathBuilder()
    foot_l = 0.0
    if ctx.style.serif == "bracketed":
        foot_l = _bowl_cap_bracketed_foot_start(b, h, ctx, stem_x=st)
    elif inlined:
        l, th, _ = _bowl_cap_stem_foot_dims(h, ctx)
        foot_l = l
        b.moveTo(-l, -th)
        b.lineTo(st + l, -th)
        b.lineTo(st + l, 0.0)
        b.lineTo(st, 0.0)
    else:
        b.moveTo(0.0, 0.0)
        b.lineTo(st, 0.0)
    for pt in ((st, y_b), (x_l, y_b), (w - hw, 0.0), foot_r, after[0]):
        b.lineTo(*pt)
    _curve(b, after)
    _curve(b, q0)
    if ctx.style.serif == "bracketed":
        _bowl_cap_bracketed_close_left(b, cap=cap, l=foot_l)
    elif inlined:
        b.lineTo(0.0, cap)
        b.lineTo(0.0, 0.0)
        b.lineTo(-foot_l, 0.0)
    else:
        b.lineTo(0.0, cap)
    b.closePath()
    _counter(b, st, x0, i3, i0)
    outline = _with_counters(b)
    if _cap_italic_sans(ctx):
        outline = _apply_italic_opening_tip_shear(
            ctx, outline, (foot_r,), stem=h.stem
        )
    return outline


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
    st = h.stem
    w = max(width * h.width, min_bowl_stems(st) * st)
    inlined = _cap_serif_inlined(c)
    o_rec = _o_rec(O) if O is not None else cap_o_metrics(c)
    outline = R_yoke(
        c,
        metrics=h,
        o_metrics_rec=o_rec,
        width=width,
        straight=straight,
        bowl=bowl,
        leg_at=leg_at,
    )
    return _pack(
        c,
        h,
        _cap_anchors(w, h, stem_serif_anchors=not inlined, stem_serif_mode="left"),
        outline,
    )


def B_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
    width: float = 0.92,
    top_scale: float = 0.9,
    straight: float = 0.45,
    waist: float = 0.53,
) -> Outline:
    """Continuous cap ``B`` body — Usage A (two stacked half bowls)."""
    h = metrics or h_cap_metrics(ctx)
    e = (o_metrics_rec or cap_o_metrics(ctx)).exponent
    st, cap, bt = h.stem, h.cap_height, h.bar
    w = max(width * h.width, min_bowl_stems(st) * st / top_scale)
    wu = top_scale * w
    m1 = waist * cap + bt / 2.0
    m0 = m1 - bt
    xl, xu = _straight_run(straight, w, st), _straight_run(straight, wu, st)
    lq3, lq0, li3, li0 = _half_bowl(xl, 0.0, m1, w, st, bt, e)
    uq3, uq0, ui3, ui0 = _half_bowl(xu, m0, cap, wu, st, bt, e)
    inside: list[Any] = []
    for hit in curveCurveIntersections(list(lq0), list(uq3)):
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

    inlined = _cap_serif_inlined(ctx)
    b = PathBuilder()
    foot_l = 0.0
    if ctx.style.serif == "bracketed":
        foot_l = _bowl_cap_bracketed_foot_start(b, h, ctx, stem_x=xl)
    elif inlined:
        l, th, _ = _bowl_cap_stem_foot_dims(h, ctx)
        foot_l = l
        b.moveTo(-l, -th)
        b.lineTo(st + l, -th)
        b.lineTo(st + l, 0.0)
        b.lineTo(xl, 0.0)
    else:
        b.moveTo(0.0, 0.0)
        b.lineTo(xl, 0.0)
    _curve(b, lq3)
    _curve(b, low_part)
    _curve(b, (low_part[3], up_part[1], up_part[2], up_part[3]))
    _curve(b, uq0)
    if ctx.style.serif == "bracketed":
        _bowl_cap_bracketed_close_left(b, cap=cap, l=foot_l)
    elif inlined:
        b.lineTo(0.0, cap)
        b.lineTo(0.0, 0.0)
        b.lineTo(-foot_l, 0.0)
    else:
        b.lineTo(0.0, cap)
    b.closePath()
    _counter(b, st, xl, li3, li0)
    _counter(b, st, xu, ui3, ui0)
    return _with_counters(b)


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
    st = h.stem
    w = max(width * h.width, min_bowl_stems(st) * st / top_scale)
    inlined = _cap_serif_inlined(c)
    o_rec = _o_rec(O) if O is not None else cap_o_metrics(c)
    outline = B_yoke(
        c,
        metrics=h,
        o_metrics_rec=o_rec,
        width=width,
        top_scale=top_scale,
        straight=straight,
        waist=waist,
    )
    return _pack(
        c,
        h,
        _cap_anchors(w, h, stem_serif_anchors=not inlined, stem_serif_mode="left"),
        outline,
    )


def _u_parts(h: HMetrics, w: float, e: float, spring: float) -> tuple[Cubic, ...]:
    """Bottom bowl quarters for ``U`` / ``J``: outer q2, q3 and inner i2, i3."""
    cx = w / 2.0
    ry = spring + h.overshoot
    ry_i = ry - h.bar
    _, _, q2, q3 = _quarters(cx, spring, w / 2.0, ry, e)
    _, _, i2, i3 = _quarters(cx, spring, w / 2.0 - h.stem, ry_i, e)
    return q2, q3, i2, i3


def _write_u_bracketed_outer(
    b: PathBuilder,
    h: HMetrics,
    ctx: DesignContext,
    *,
    w: float,
    cap: float,
    y_s: float,
    q2: Cubic,
    q3: Cubic,
    i2: Cubic,
    i3: Cubic,
) -> None:
    t = h.stem
    l, th, bracket_r = _h_cap_foot_dims(h, ctx)
    b.moveTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, y_s)
    _curve(b, q2)
    _curve(b, q3)
    b.lineTo(w, cap)
    b.lineTo(w + l, cap)
    _append_upward_cap_foot_pad(b, w - t - l, w + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(w - t, cap)
    b.lineTo(w - t, y_s)
    _curve(b, _rev(i3))
    _curve(b, _rev(i2))
    b.lineTo(t, cap)
    b.lineTo(t + l, cap)
    b.lineTo(-l, cap)
    b.closePath()


def U_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
    width: float = 0.96,
    spring: float = 0.38,
) -> Outline:
    """Continuous cap ``U`` body — Usage A (two stems + bottom bowl)."""
    h = metrics or h_cap_metrics(ctx)
    e = (o_metrics_rec or cap_o_metrics(ctx)).exponent
    st, cap = h.stem, h.cap_height
    w = max(width * h.width, min_bowl_stems(st) * st)
    y_s = spring * cap
    q2, q3, i2, i3 = _u_parts(h, w, e, y_s)
    inlined = _cap_serif_inlined(ctx)

    b = PathBuilder()
    if ctx.style.serif == "bracketed":
        _write_u_bracketed_outer(
            b, h, ctx, w=w, cap=cap, y_s=y_s, q2=q2, q3=q3, i2=i2, i3=i3
        )
    elif inlined:
        from typekernel.parts.serifs import serif_metrics

        length, thick, _ = serif_metrics(ctx)
        l = min(length, st * 0.48)
        th = min(thick, cap * 0.1, st * 0.18)
        b.moveTo(-l, cap + th)
        b.lineTo(st + l, cap + th)
        b.lineTo(st + l, cap)
        b.lineTo(0.0, cap)
        b.lineTo(0.0, y_s)
        _curve(b, q2)
        _curve(b, q3)
        b.lineTo(w, cap)
        b.lineTo(w + l, cap)
        b.lineTo(w + l, cap + th)
        b.lineTo(w - st - l, cap + th)
        b.lineTo(w - st - l, cap)
        b.lineTo(w - st, cap)
        b.lineTo(w - st, y_s)
        _curve(b, _rev(i3))
        _curve(b, _rev(i2))
        b.lineTo(st, cap)
        b.lineTo(st + l, cap)
        b.lineTo(st + l, cap + th)
        b.lineTo(-l, cap + th)
        b.closePath()
    elif _cap_italic_sans(ctx):
        fr = min(ctx.join_radius * 0.35, st * 0.14)
        fr = max(fr, 1.0)
        b.moveTo(fr, cap)
        b.curveTo(fr - fr * KAPPA, cap, 0.0, cap - fr + fr * KAPPA, 0.0, cap - fr)
        b.lineTo(0.0, y_s)
        _curve(b, q2)
        _curve(b, q3)
        b.lineTo(w, cap - fr)
        b.curveTo(w, cap - fr + fr * KAPPA, w - fr + fr * KAPPA, cap, w - fr, cap)
        b.lineTo(w - st + fr, cap)
        b.curveTo(
            w - st + fr - fr * KAPPA,
            cap,
            w - st,
            cap - fr + fr * KAPPA,
            w - st,
            cap - fr,
        )
        b.lineTo(w - st, y_s)
        _curve(b, _rev(i3))
        _curve(b, _rev(i2))
        b.lineTo(st, cap - fr)
        b.curveTo(st, cap - fr + fr * KAPPA, st - fr + fr * KAPPA, cap, st - fr, cap)
        b.lineTo(fr, cap)
        b.closePath()
    else:
        b.moveTo(0.0, cap)
        b.lineTo(0.0, y_s)
        _curve(b, q2)
        _curve(b, q3)
        b.lineTo(w, cap)
        b.lineTo(w - st, cap)
        b.lineTo(w - st, y_s)
        _curve(b, _rev(i3))
        _curve(b, _rev(i2))
        b.lineTo(st, cap)
        b.closePath()
    return _ccw(b.build())


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
    o_rec = _o_rec(O) if O is not None else cap_o_metrics(c)
    st, cap = h.stem, h.cap_height
    w = max(width * h.width, min_bowl_stems(st) * st)
    inlined = _cap_serif_inlined(c)
    half = st / 2.0
    anchors: dict[str, Pt] = {
        "top": (w / 2.0, cap),
        "bottom": (w / 2.0, 0.0),
    }
    if _cap_stem_serif_anchors_enabled(c, baked=inlined):
        anchors.update(
            {
                "stem_L_b": (half, 0.0),
                "stem_L_t": (half, cap),
                "stem_R_b": (w - half, 0.0),
                "stem_R_t": (w - half, cap),
            }
        )
    outline = U_yoke(
        c, metrics=h, o_metrics_rec=o_rec, width=width, spring=spring
    )
    return _pack(c, h, anchors, outline)


def J_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    o_metrics_rec: OMetrics | None = None,
    width: float = 0.72,
    spring: float = 0.38,
    hook: float = 0.55,
) -> Outline:
    """Continuous cap ``J`` body — Usage A (right stem + hook bowl)."""
    h = metrics or h_cap_metrics(ctx)
    e = (o_metrics_rec or cap_o_metrics(ctx)).exponent
    st, cap = h.stem, h.cap_height
    w = max(width * h.width, min_bowl_stems(st) * st)
    y_s = spring * cap
    q2, q3, i2, i3 = _u_parts(h, w, e, y_s)
    cx = w / 2.0
    hook_v = hook * (opening_closure(ctx, 0.55) / 0.55)
    x_t = cx - hook_v * (w / 2.0 - st)
    outer = _cut(q2, x_t, horizontal=False)[1]
    inner = _cut(i2, x_t, horizontal=False)[1]

    inlined = _cap_serif_inlined(ctx)
    l, th, bracket_r = _h_cap_foot_dims(h, ctx) if inlined else (0.0, 0.0, 0.0)
    b = PathBuilder()
    if ctx.style.serif == "bracketed":
        b.moveTo(w + l, cap)
        _append_upward_cap_foot_pad(
            b, w - st - l, w + l, cap, th, bracket_r, bracketed=True
        )
        b.lineTo(w - st, cap)
    elif inlined:
        b.moveTo(w + l, cap + th)
        b.lineTo(w - st - l, cap + th)
        b.lineTo(w - st - l, cap)
        b.lineTo(w - st, cap)
    else:
        fr = min(ctx.join_radius * 0.35, st * 0.14)
        fr = max(fr, 1.0)
        b.moveTo(w, cap - fr)
        b.curveTo(w, cap - fr + fr * KAPPA, w - fr + fr * KAPPA, cap, w - fr, cap)
        b.lineTo(w - st + fr, cap)
        b.curveTo(
            w - st + fr - fr * KAPPA,
            cap,
            w - st,
            cap - fr + fr * KAPPA,
            w - st,
            cap - fr,
        )
    b.lineTo(w - st, y_s)
    _curve(b, _rev(i3))
    _curve(b, _rev(inner))
    p0, p1, _, _ = inner
    q0, q1, _, _ = outer
    ji, jo = p0, q0
    inx, iny = ji[0] - p1[0], ji[1] - p1[1]
    outx, outy = q1[0] - jo[0], q1[1] - jo[1]
    lin = math.hypot(inx, iny) or 1.0
    lout = math.hypot(outx, outy) or 1.0
    inx, iny = inx / lin, iny / lin
    outx, outy = outx / lout, outy / lout
    dist = math.hypot(jo[0] - ji[0], jo[1] - ji[1])
    tension = 0.38
    b.curveTo(
        ji[0] + inx * dist * tension,
        ji[1] + iny * dist * tension,
        jo[0] - outx * dist * tension,
        jo[1] - outy * dist * tension,
        jo[0],
        jo[1],
    )
    _curve(b, outer)
    _curve(b, q3)
    if inlined:
        b.lineTo(w + l, cap)
        if ctx.style.serif == "slab":
            b.lineTo(w + l, cap + th)
            b.lineTo(w - st - l, cap + th)
    b.closePath()
    outline = _ccw(b.build())
    if _cap_italic_sans(ctx):
        tip = ((ji[0] + jo[0]) * 0.5, (ji[1] + jo[1]) * 0.5)
        outline = _apply_italic_opening_tip_shear(ctx, outline, (tip,), stem=st)
    return outline


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
    o_rec = _o_rec(O) if O is not None else cap_o_metrics(c)
    st, cap = h.stem, h.cap_height
    w = max(width * h.width, min_bowl_stems(st) * st)
    cx = w / 2.0
    inlined = _cap_serif_inlined(c)
    half = w - st / 2.0
    anchors: dict[str, Pt] = {"top": (half, cap), "bottom": (cx, 0.0)}
    if _cap_stem_serif_anchors_enabled(c, baked=inlined):
        anchors["stem_R_t"] = (half, cap)
    outline = J_yoke(
        c,
        metrics=h,
        o_metrics_rec=o_rec,
        width=width,
        spring=spring,
        hook=hook,
    )
    return _pack(c, h, anchors, outline)


def _diag_cap(
    H: ComposedGlyph, ctx: DesignContext | None, width: float, pts: list[Pt]
) -> ComposedGlyph:
    c = ctx or H.context
    h = _h_record(H)
    return _pack(c, h, _cap_anchors(width, h), _polygon(pts))


def _v_cap_foot_dims(h: HMetrics, ctx: DesignContext, apex_x: float) -> tuple[float, float, float]:
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    l = min(length * 0.35, apex_x * 0.28, h.stem * 0.28)
    th = min(thick * 0.55, h.cap_height * 0.04, h.stem * 0.1)
    return l, th, bracket_r


def _finish_baseline_foot_pad(
    b: PathBuilder,
    xl: float,
    xr: float,
    th: float,
    bracket_r: float,
    *,
    bracketed: bool,
) -> None:
    """Complete a baseline foot pad from ``(xl, -th)``; ends at ``(xr, 0)``."""
    if not bracketed:
        b.lineTo(xr, -th)
        b.lineTo(xr, 0.0)
        return
    span_x = xr - xl
    r = min(bracket_r, span_x * 0.4, th * 0.45)
    if r < 0.35:
        b.lineTo(xr, -th)
        b.lineTo(xr, 0.0)
        return
    b.lineTo(xr - r, -th)
    b.curveTo(
        xr - r + r * KAPPA,
        -th,
        xr,
        -th + r - r * KAPPA,
        xr,
        -th + r,
    )
    b.lineTo(xr, 0.0)


def _finish_foot_pad_below(
    b: PathBuilder,
    xl: float,
    xr: float,
    y: float,
    th: float,
    bracket_r: float,
    *,
    bracketed: bool,
) -> None:
    """Complete a foot pad below ``y`` from ``(xl, y)``; ends at ``(xr, y)``."""
    if not bracketed:
        b.lineTo(xl, y - th)
        b.lineTo(xr, y - th)
        b.lineTo(xr, y)
        return
    span_x = xr - xl
    r = min(bracket_r, span_x * 0.4, th * 0.45)
    if r < 0.35:
        b.lineTo(xl, y - th)
        b.lineTo(xr, y - th)
        b.lineTo(xr, y)
        return
    b.lineTo(xl, y - th)
    b.lineTo(xr - r, y - th)
    b.curveTo(
        xr - r + r * KAPPA,
        y - th,
        xr,
        y - th + r - r * KAPPA,
        xr,
        y - th + r,
    )
    b.lineTo(xr, y)


def _append_baseline_foot_pad(
    b: PathBuilder,
    xl: float,
    xr: float,
    th: float,
    bracket_r: float,
    *,
    bracketed: bool,
) -> None:
    """Foot pad below the baseline from ``xl`` to ``xr``; ends at ``(xr, 0)``."""
    b.lineTo(xl, -th)
    _finish_baseline_foot_pad(b, xl, xr, th, bracket_r, bracketed=bracketed)


def _append_upward_cap_foot_pad(
    b: PathBuilder,
    xl: float,
    xr: float,
    y: float,
    th: float,
    bracket_r: float,
    *,
    bracketed: bool,
) -> None:
    """Foot pad above ``y`` from ``xl`` to ``xr``; ends at ``(xl, y)`` (after ``(xr, y)``)."""
    b.lineTo(xr, y + th)
    if not bracketed:
        b.lineTo(xl, y + th)
        b.lineTo(xl, y)
        return
    span_x = xr - xl
    r = min(bracket_r, span_x * 0.4, th * 0.45)
    if r < 0.35:
        b.lineTo(xl, y + th)
        b.lineTo(xl, y)
        return
    b.lineTo(xl + r, y + th)
    b.curveTo(
        xl + r - r * KAPPA,
        y + th,
        xl,
        y + th - r + r * KAPPA,
        xl,
        y + th - r,
    )
    b.lineTo(xl, y)


def _append_v_cap_foot_pad(
    b: PathBuilder,
    apex_x: float,
    l: float,
    th: float,
    bracket_r: float,
    *,
    bracketed: bool,
) -> None:
    """Bottom foot pad at one ``V`` apex (ends on ``(apex_x + l, 0)``)."""
    _append_baseline_foot_pad(
        b, apex_x - l, apex_x + l, th, bracket_r, bracketed=bracketed
    )


def _v_cap_slab_points(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> list[Pt]:
    """Slab feet on the flat ``V`` apex only (top stays sharp for lint)."""
    a0 = base[1][0]
    w = base[3][0]
    l, th, _ = _v_cap_foot_dims(h, ctx, a0)
    return [
        base[0],
        base[1],
        (a0 - l, -th),
        (a0 + l, -th),
        (a0 + l, 0.0),
        base[2],
        (w - a0 - l, -th),
        (w - a0 + l, -th),
        (w - a0 + l, 0.0),
        base[3],
        base[4],
        base[5],
        base[6],
    ]


def _v_cap_bracketed_outline(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> Outline:
    """Bracketed ``V``: slab foot pads with inner cubic fillets (fixed topology)."""
    a0 = base[1][0]
    w = base[3][0]
    l, th, bracket_r = _v_cap_foot_dims(h, ctx, a0)
    b = PathBuilder()
    b.moveTo(*base[0])
    b.lineTo(*base[1])
    _append_v_cap_foot_pad(b, a0, l, th, bracket_r, bracketed=True)
    b.lineTo(*base[2])
    _append_v_cap_foot_pad(b, w - a0, l, th, bracket_r, bracketed=True)
    for p in base[3:]:
        b.lineTo(*p)
    b.closePath()
    return _ccw(b.build())


def V_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.98,
) -> Outline:
    """Continuous cap ``V`` body — Usage A (diagonal crotch flats sealed)."""
    h = metrics or h_cap_metrics(ctx)
    w_frac = width
    s = ctx.stem
    if s <= 72.0 and (
        0.95 <= ctx.contrast < 1.0
        or (ctx.contrast >= 1.0 and ctx.roundness < 0.26)
    ):
        w_frac += 0.02
    if 142.0 <= s <= 158.0:
        w_frac += 0.04
    w = w_frac * h.width
    bump = ctx.sharp_overshoot
    base = v_points(h.stem, h.cap_height, w, ctx.contrast, top_overshoot=bump)
    baked = _cap_serif_inlined(ctx)
    if baked and ctx.style.serif == "bracketed":
        return _v_cap_bracketed_outline(h, ctx, base)
    if baked:
        return _polygon(_v_cap_slab_points(h, ctx, base))
    if _cap_italic_sans(ctx):
        bias = 0.11 * w
        pts = list(base)
        pts[1] = (pts[1][0] + bias * 0.25, pts[1][1])
        pts[2] = (pts[2][0] + bias * 0.55, pts[2][1])
        pts[5] = (pts[5][0] + bias * 0.45, pts[5][1])
        return _soft_corner_polygon(pts, frozenset({5}), h.stem * 0.38)
    return _polygon(base)


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
    baked = _cap_serif_inlined(c)
    anchors = _cap_anchors(
        w,
        h,
        stem_serif_anchors=_cap_stem_serif_anchors_enabled(c, baked=baked, diagonal=True),
    )
    return _pack(c, h, anchors, V_yoke(c, metrics=h, width=width))


def _w_cap_foot_dims(h: HMetrics, ctx: DesignContext, apex_x: float) -> tuple[float, float, float]:
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    l = min(length * 0.35, apex_x * 0.28, h.stem * 0.28)
    th = min(thick * 0.55, h.cap_height * 0.04, h.stem * 0.1)
    return l, th, bracket_r


def _w_cap_slab_points(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> list[Pt]:
    """Slab feet on the two outer ``W`` apex flats (bottom only)."""
    a1l = base[1][0]
    a1r = base[2][0]
    ww = base[6][0]
    l, th, _ = _w_cap_foot_dims(h, ctx, a1l)
    return [
        base[0],
        base[1],
        (a1l - l, -th),
        (a1r + l, -th),
        (a1r + l, 0.0),
        base[2],
        base[3],
        base[4],
        (ww - a1r - l, -th),
        (ww - a1l + l, -th),
        (ww - a1l + l, 0.0),
        base[5],
        base[6],
        base[7],
        base[8],
        base[9],
        base[10],
        base[11],
        base[12],
    ]


def _w_cap_bracketed_outline(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> Outline:
    a1l, a1r = base[1][0], base[2][0]
    ww = base[6][0]
    l, th, bracket_r = _w_cap_foot_dims(h, ctx, a1l)
    b = PathBuilder()
    b.moveTo(*base[0])
    b.lineTo(*base[1])
    _append_baseline_foot_pad(b, a1l - l, a1r + l, th, bracket_r, bracketed=True)
    b.lineTo(*base[2])
    for p in base[3:5]:
        b.lineTo(*p)
    _append_baseline_foot_pad(b, ww - a1r - l, ww - a1l + l, th, bracket_r, bracketed=True)
    for p in base[5:]:
        b.lineTo(*p)
    b.closePath()
    return _ccw(b.build())


def W_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 1.4,
) -> Outline:
    """Continuous cap ``W`` body — Usage A (crotch flats sealed via ``w_points``)."""
    h = metrics or h_cap_metrics(ctx)
    w_frac = width
    s = ctx.stem
    if s <= 72.0:
        if ctx.contrast < 0.85:
            w_frac += 0.02
        elif 0.86 <= ctx.contrast <= 0.94 and ctx.aperture < 0.68:
            w_frac -= 0.02
    if 168.0 <= s <= 192.0:
        w_frac += 0.02
    if ctx.style.serif == "bracketed" and s <= 78.0:
        w_frac += 0.085
    w = w_frac * h.width
    bump = ctx.sharp_overshoot
    base = w_points(h.stem, h.cap_height, w, ctx.contrast, top_overshoot=bump)
    baked = _cap_serif_inlined(ctx)
    if baked and ctx.style.serif == "bracketed":
        return _w_cap_bracketed_outline(h, ctx, base)
    if baked:
        return _polygon(_w_cap_slab_points(h, ctx, base))
    if _cap_italic_sans(ctx):
        return _soft_corner_polygon(base, frozenset({3, 8, 11}), h.stem * 0.28)
    return _polygon(base)


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
    if c.style.serif == "bracketed" and s <= 78.0:
        w_frac += 0.085
    w = w_frac * h.width
    baked = _cap_serif_inlined(c)
    anchors = _cap_anchors(
        w,
        h,
        stem_serif_anchors=_cap_stem_serif_anchors_enabled(c, baked=baked, diagonal=True),
    )
    return _pack(c, h, anchors, W_yoke(c, metrics=h, width=width))


def _x_cap_foot_dims(h: HMetrics, ctx: DesignContext, hw: float) -> tuple[float, float, float]:
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    cap = h.cap_height
    l = min(length * 0.42, hw * 0.28, h.stem * 0.32)
    th = min(thick * 0.65, cap * 0.05, h.stem * 0.12)
    return l, th, bracket_r


def _x_cap_slab_points(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> list[Pt]:
    """Slab feet on the lower-left and upper-right outer corners of cap ``X``."""
    cap = h.cap_height
    w = base[6][0]
    hw = base[3][0]
    l, th, _ = _x_cap_foot_dims(h, ctx, hw)
    return [
        base[0],
        base[1],
        (-l, -th),
        (hw + l, -th),
        (hw + l, 0.0),
        base[3],
        base[4],
        base[5],
        base[6],
        base[7],
        base[8],
        (w + l, cap),
        (w + l, cap + th),
        (w - hw - l, cap + th),
        (w - hw - l, cap),
        base[9],
        base[10],
        base[11],
    ]


def _x_cap_bracketed_outline(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> Outline:
    cap = h.cap_height
    w = base[6][0]
    hw = base[3][0]
    l, th, bracket_r = _x_cap_foot_dims(h, ctx, hw)
    b = PathBuilder()
    b.moveTo(*base[0])
    b.lineTo(*base[1])
    _append_baseline_foot_pad(b, -l, hw + l, th, bracket_r, bracketed=True)
    for p in base[3:9]:
        b.lineTo(*p)
    b.lineTo(w + l, cap)
    _append_upward_cap_foot_pad(b, w - hw - l, w + l, cap, th, bracket_r, bracketed=True)
    for p in base[9:]:
        b.lineTo(*p)
    b.closePath()
    return _ccw(b.build())


def X_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.92,
) -> Outline:
    """Continuous cap ``X`` body — Usage A (waist crotches sealed)."""
    h = metrics or h_cap_metrics(ctx)
    w_frac = width
    s = ctx.stem
    if 100.0 <= s <= 118.0:
        w_frac += 0.011
    if ctx.style.serif in ("slab", "bracketed"):
        if s <= 78.0:
            w_frac += 0.07
        if 100.0 <= s <= 118.0:
            w_frac += 0.04
        if 138.0 <= s <= 162.0:
            w_frac += 0.05
    w = w_frac * h.width
    if ctx.style.serif == "slab" and h.stem >= 150.0:
        extreme = max(0.0, min(1.0, (h.stem - 150.0) / 70.0))
        diag_w = 1.0 - 0.14 * extreme
    else:
        diag_w = 1.0
    base = x_points(h.stem, h.cap_height, w, ctx.contrast, weight=diag_w)
    baked = _cap_serif_inlined(ctx)
    if baked and ctx.style.serif == "bracketed":
        return _x_cap_bracketed_outline(h, ctx, base)
    if baked:
        return _polygon(_x_cap_slab_points(h, ctx, base))
    if _cap_italic_sans(ctx):
        dy = 0.07 * h.cap_height
        pts = list(base)
        pts[1] = (pts[1][0], pts[1][1] + dy)
        pts[7] = (pts[7][0], pts[7][1] + dy)
        pts[4] = (pts[4][0], pts[4][1] + dy * 0.5)
        pts[10] = (pts[10][0], pts[10][1] + dy * 0.5)
        return _soft_corner_polygon(pts, frozenset({1, 4, 7, 10}), h.stem * 0.22)
    return _polygon(base)


def X_from_H(
    H: ComposedGlyph, ctx: DesignContext | None = None, *, width: float = 0.92
) -> ComposedGlyph:
    """``X``: two compensated diagonals crossing at mid cap height."""
    h, c = _h_record(H), ctx or H.context
    w_frac = width
    s = c.stem
    if 100.0 <= s <= 118.0:
        w_frac += 0.011
    if c.style.serif in ("slab", "bracketed"):
        if s <= 78.0:
            w_frac += 0.07
        if 100.0 <= s <= 118.0:
            w_frac += 0.04
        if 138.0 <= s <= 162.0:
            w_frac += 0.05
    w = w_frac * h.width
    baked = _cap_serif_inlined(c)
    anchors = _cap_anchors(
        w,
        h,
        stem_serif_anchors=_cap_stem_serif_anchors_enabled(c, baked=baked, diagonal=True),
    )
    return _pack(c, h, anchors, X_yoke(c, metrics=h, width=width))


def _z_cap_foot_dims(h: HMetrics, ctx: DesignContext) -> tuple[float, float, float]:
    cap, bt = h.cap_height, h.bar
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    l = min(length, bt * 0.55, h.stem * 0.48)
    th = min(thick, bt * 0.5, cap * 0.08)
    return l, th, bracket_r


def _z_cap_slab_points(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> list[Pt]:
    """Slab feet on the lower-left and upper-left (and top-right cap) of cap ``Z``."""
    cap, bt = h.cap_height, h.bar
    w = base[1][0]
    l, th, _ = _z_cap_foot_dims(h, ctx)
    hw = base[3][0]
    return [
        (-l, -th),
        (bt + l, -th),
        (bt + l, 0.0),
        (w, 0.0),
        (w, bt),
        (hw, bt),
        (w, cap - bt),
        (w, cap),
        (w + l, cap),
        (w + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, cap - bt),
        (w - hw, cap - bt),
        (0.0, bt),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def _z_cap_bracketed_outline(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> Outline:
    cap, bt = h.cap_height, h.bar
    w = base[1][0]
    hw = base[3][0]
    l, th, bracket_r = _z_cap_foot_dims(h, ctx)
    b = PathBuilder()
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, bt + l, th, bracket_r, bracketed=True)
    b.lineTo(w, 0.0)
    b.lineTo(w, bt)
    b.lineTo(hw, bt)
    b.lineTo(w, cap - bt)
    b.lineTo(w, cap)
    b.lineTo(w + l, cap)
    _append_upward_cap_foot_pad(b, -l, w + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, cap - bt)
    b.lineTo(w - hw, cap - bt)
    b.lineTo(0.0, bt)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()
    return _ccw(b.build())


def Z_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.88,
) -> Outline:
    """Continuous cap ``Z`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    w = width * h.width
    base = z_points(h.stem, h.bar, h.cap_height, w, ctx.contrast)
    baked = _cap_serif_inlined(ctx)
    if baked and ctx.style.serif == "bracketed":
        return _z_cap_bracketed_outline(h, ctx, base)
    if baked:
        return _polygon(_z_cap_slab_points(h, ctx, base))
    if _cap_italic_sans(ctx):
        return _soft_corner_polygon(base, frozenset({3, 8}), h.stem * 0.30)
    return _polygon(base)


def Z_from_H(
    H: ComposedGlyph, ctx: DesignContext | None = None, *, width: float = 0.88
) -> ComposedGlyph:
    """``Z``: ``H``-bar-thick top and foot joined by one compensated diagonal."""
    h, c = _h_record(H), ctx or H.context
    w = width * h.width
    baked = _cap_serif_inlined(c)
    anchors = _cap_anchors(
        w,
        h,
        stem_serif_anchors=_cap_stem_serif_anchors_enabled(c, baked=baked, diagonal=True),
    )
    return _pack(c, h, anchors, Z_yoke(c, metrics=h, width=width))


def _k_cap_foot_dims(h: HMetrics, ctx: DesignContext) -> tuple[float, float, float]:
    from typekernel.parts.serifs import serif_metrics
    from typekernel.parts.weight_relief import stem_weight_fraction

    length, thick, bracket_r = serif_metrics(ctx)
    t = h.stem
    l = min(length, t * 0.5)
    th = min(thick, h.cap_height * 0.1, t * 0.2)
    if ctx.style.serif == "bracketed":
        heavy = stem_weight_fraction(t)
        th *= 1.0 - 0.14 * heavy
        l *= 1.0 - 0.06 * heavy
    return l, th, bracket_r


def _k_cap_slab_points(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> list[Pt]:
    """Bake left-stem slab feet/caps onto cap ``k_points`` outline."""
    t, cap = h.stem, h.cap_height
    l, th, _ = _k_cap_foot_dims(h, ctx)
    middle = base[1:10]
    return [
        (-l, -th),
        (t + l, -th),
        (t + l, 0.0),
        *middle,
        (t + l, cap),
        (t + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def _k_cap_bracketed_outline(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> Outline:
    t, cap = h.stem, h.cap_height
    l, th, bracket_r = _k_cap_foot_dims(h, ctx)
    b = PathBuilder()
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    for p in base[1:10]:
        b.lineTo(*p)
    b.lineTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()
    return _ccw(b.build())


def K_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.92,
    vertex: float = 0.42,
) -> Outline:
    """Continuous cap ``K`` body — Usage A (arm/leg crotch sealed via ``k_points``)."""
    h = metrics or h_cap_metrics(ctx)
    s = ctx.stem
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
    if ctx.style.serif in ("slab", "bracketed"):
        if s <= 40.0:
            w_frac += 0.08
        if 100.0 <= s <= 118.0:
            w_frac += 0.04
            if ctx.style.serif == "bracketed":
                w_frac += 0.04
        if 138.0 <= s <= 162.0:
            w_frac += 0.06
            vertex_eff = max(vertex_eff, 0.44)
        if 168.0 <= s <= 192.0:
            w_frac += 0.03
            vertex_eff = max(vertex_eff, 0.44)
    w = w_frac * h.width
    cap = h.cap_height
    if _cap_italic_sans(ctx):
        vertex_eff = min(0.58, max(vertex_eff, 0.50))
    base = k_points(h.stem, cap, cap, w, ctx.contrast, vertex=vertex_eff)
    baked = _cap_serif_inlined(ctx)
    if baked and ctx.style.serif == "bracketed":
        return _k_cap_bracketed_outline(h, ctx, base)
    if baked:
        return _polygon(_k_cap_slab_points(h, ctx, base))
    if _cap_italic_sans(ctx):
        outline = _soft_corner_polygon(base, frozenset({2, 5, 8}), h.stem * 0.34)
        return _apply_italic_opening_tip_shear(
            ctx, outline, ((w - h.stem * 0.15, cap * 0.92),), stem=h.stem
        )
    return _polygon(base)


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
    if s <= 72.0:
        w_frac += 0.07
    elif s < 80.0:
        w_frac += 0.07 * max(0.0, (80.0 - s) / 50.0)
    if 100.0 <= s <= 118.0:
        w_frac += 0.038
    if 142.0 <= s <= 158.0:
        w_frac += 0.024
    if 168.0 <= s <= 192.0:
        w_frac += 0.042
    if c.style.serif in ("slab", "bracketed"):
        if s <= 40.0:
            w_frac += 0.08
        if 100.0 <= s <= 118.0:
            w_frac += 0.04
            if c.style.serif == "bracketed":
                w_frac += 0.04
        if 138.0 <= s <= 162.0:
            w_frac += 0.06
        if 168.0 <= s <= 192.0:
            w_frac += 0.03
    w = w_frac * h.width
    baked = _cap_serif_inlined(c)
    anchors = _cap_anchors(
        w,
        h,
        stem_serif_anchors=_cap_stem_serif_anchors_enabled(c, baked=baked, diagonal=True),
    )
    return _pack(c, h, anchors, K_yoke(c, metrics=h, width=width, vertex=vertex))


def _a_cap_foot_dims(h: HMetrics, ctx: DesignContext, hw: float) -> tuple[float, float, float]:
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    t = h.stem
    l = min(length * 0.42, hw * 0.55, t * 0.48)
    th = min(thick * 0.65, h.cap_height * 0.05, t * 0.18)
    return l, th, bracket_r


def _a_cap_slab_outer(
    h: HMetrics, ctx: DesignContext, hw: float, w: float, base: list[Pt]
) -> list[Pt]:
    """Slab feet on the two baseline stems of cap ``A`` (apex stays sharp)."""
    l, th, _ = _a_cap_foot_dims(h, ctx, hw)
    return [
        (-l, -th),
        (hw + l, -th),
        (hw + l, 0.0),
        base[2],
        base[3],
        (w - hw - l, -th),
        (w + l, -th),
        (w + l, 0.0),
        base[5],
        base[6],
        base[7],
        (-l, 0.0),
    ]


def _write_a_cap_bracketed_outer(
    b: PathBuilder,
    h: HMetrics,
    ctx: DesignContext,
    hw: float,
    w: float,
    f: float,
    peak: float,
    y0: float,
    *,
    left_at_y0: float,
) -> None:
    """Bracketed ``A`` outer contour with cubic foot fillets (fixed topology)."""
    l, th, bracket_r = _a_cap_foot_dims(h, ctx, hw)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, hw + l, th, bracket_r, bracketed=True)
    b.lineTo(hw, 0.0)
    b.lineTo(left_at_y0, y0)
    b.lineTo(w - hw - l, -th)
    _finish_baseline_foot_pad(b, w - hw - l, w + l, th, bracket_r, bracketed=True)
    b.lineTo(w - hw, 0.0)
    b.lineTo(w, 0.0)
    b.lineTo((w + f) / 2.0, peak)
    b.lineTo((w - f) / 2.0, peak)
    b.lineTo(-l, 0.0)
    b.closePath()


def A_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 1.02,
    apex: float = 0.35,
    bar: float = 0.28,
) -> Outline:
    """Continuous cap ``A`` body (outer + triangular counter) — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    w, cap = max(width * h.width, 3.2 * h.stem), h.cap_height
    peak = cap + ctx.sharp_overshoot
    f = apex * h.stem
    a = (w - f) / 2.0
    extreme = max(0.0, min(1.0, (h.stem - 130.0) / 90.0)) if h.stem >= 130.0 else 0.0
    diag_w = 1.0 - 0.16 * extreme
    hw = _hwidth(h.stem, ctx.contrast, a, cap, weight=diag_w)
    crotch = cap * (w - 2.0 * hw) / (2.0 * a)
    y0 = bar * cap - h.bar / 2.0
    y1 = min(y0 + h.bar, crotch - 0.5 * h.stem)
    if not (hw > f / 2.0 and 0.0 < y0 < y1 < crotch < cap):
        raise ValueError("A strokes do not fit this width; widen it or thin the stem")

    def left(y: float) -> float:
        return hw + a * y / cap

    def right(y: float) -> float:
        return w - hw - a * y / cap

    baked = _cap_serif_inlined(ctx)
    base_outer = [
        (0.0, 0.0),
        (hw, 0.0),
        (left(y0), y0),
        (right(y0), y0),
        (w - hw, 0.0),
        (w, 0.0),
        ((w + f) / 2.0, peak),
        ((w - f) / 2.0, peak),
    ]
    if baked and ctx.style.serif == "bracketed":
        b = PathBuilder()
        _write_a_cap_bracketed_outer(
            b, h, ctx, hw, w, f, peak, y0, left_at_y0=left(y0)
        )
        ctr = _truncate_crotch(
            [(left(y1), y1), (w / 2.0, crotch), (right(y1), y1)],
            1,
            _crotch_seal_flat(h.stem),
        )
        b.moveTo(*ctr[0])
        for pt in ctr[1:]:
            b.lineTo(*pt)
        b.closePath()
        return _with_counters(b)
    if _cap_italic_sans(ctx) and not baked:
        outer = _soft_corner_polygon(base_outer, frozenset({6, 7}), h.stem * 0.20)
        ctr_pts = _truncate_crotch(
            [(left(y1), y1), (w / 2.0, crotch), (right(y1), y1)],
            1,
            _crotch_seal_flat(h.stem),
        )
        # Soft the sealed flat endpoints (indices 1,2 after truncate).
        counter = _soft_corner_polygon(
            ctr_pts,
            frozenset({1, 2}),
            h.stem * 0.30,
        )
        oc = outer.contours[0]
        if signed_area(oc) < 0:
            oc = reverse_contour(oc)
        cc = counter.contours[0]
        if signed_area(cc) > 0:
            cc = reverse_contour(cc)
        return Outline((oc, cc))
    b = PathBuilder()
    outer_pts = _a_cap_slab_outer(h, ctx, hw, w, base_outer) if baked else base_outer
    for i, pt in enumerate(outer_pts):
        (b.moveTo if i == 0 else b.lineTo)(*pt)
    b.closePath()
    ctr = _truncate_crotch(
        [(left(y1), y1), (w / 2.0, crotch), (right(y1), y1)],
        1,
        _crotch_seal_flat(h.stem),
    )
    b.moveTo(*ctr[0])
    for pt in ctr[1:]:
        b.lineTo(*pt)
    b.closePath()
    return _with_counters(b)


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
    w = max(width * h.width, 3.2 * h.stem)
    baked = _cap_serif_inlined(c)
    anchors = _cap_anchors(
        w, h, stem_serif_anchors=_cap_stem_serif_anchors_enabled(c, baked=baked, diagonal=True)
    )
    outline = A_yoke(c, metrics=h, width=width, apex=apex, bar=bar)
    return _pack(c, h, anchors, outline)


def _y_cap_foot_dims(
    h: HMetrics, ctx: DesignContext, base: list[Pt]
) -> tuple[float, float, float, float, float, float, float, float]:
    cap = h.cap_height
    s0 = base[2][0]
    s1 = base[3][0]
    t = s1 - s0
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    y_side = base[1][1]
    l = min(length * 0.42, t * 0.48, h.stem * 0.32)
    th = min(thick * 0.65, cap * 0.05, y_side * 0.2, t * 0.18)
    w = base[5][0]
    hw = base[8][0]
    return l, th, bracket_r, s0, s1, w, hw, cap


def _y_cap_slab_points(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> list[Pt]:
    """Slab feet on the ``Y`` stem and caps on the upper outer arms."""
    l, th, _, s0, s1, w, hw, cap = _y_cap_foot_dims(h, ctx, base)
    return [
        (-l, -th),
        (s1 + l, -th),
        (s1 + l, 0.0),
        base[3],
        base[4],
        base[5],
        (w + l, cap),
        (w + l, cap + th),
        (w - hw - l, cap + th),
        (w - hw - l, cap),
        base[6],
        base[7],
        base[8],
        (hw + l, cap),
        (hw + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        base[0],
        base[1],
        (s0 - l, 0.0),
        (-l, 0.0),
    ]


def _y_cap_bracketed_outline(h: HMetrics, ctx: DesignContext, base: list[Pt]) -> Outline:
    l, th, bracket_r, s0, s1, w, hw, cap = _y_cap_foot_dims(h, ctx, base)
    b = PathBuilder()
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, s1 + l, th, bracket_r, bracketed=True)
    b.lineTo(*base[3])
    b.lineTo(*base[4])
    b.lineTo(*base[5])
    b.lineTo(w + l, cap)
    _append_upward_cap_foot_pad(b, w - hw - l, w + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(*base[6])
    b.lineTo(*base[7])
    b.lineTo(*base[8])
    b.lineTo(hw + l, cap)
    _append_upward_cap_foot_pad(b, -l, hw + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(*base[0])
    b.lineTo(*base[1])
    b.lineTo(s0 - l, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()
    return _ccw(b.build())


def Y_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.98,
    junction: float = 0.42,
) -> Outline:
    """Continuous cap ``Y`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    junction_eff = junction
    if 142.0 <= ctx.stem <= 158.0:
        junction_eff = max(junction_eff, 0.45)
    w, cap, st = width * h.width, h.cap_height, h.stem
    yj = junction_eff * cap
    if ctx.style.serif == "slab" and st >= 175.0:
        extreme = max(0.0, min(1.0, (st - 175.0) / 45.0))
        diag_w = 1.0 - 0.12 * extreme
    else:
        diag_w = 1.0
    hw = _hwidth(st, ctx.contrast, w / 2.0 - st / 2.0, cap - yj, weight=diag_w)
    s0, s1 = (w - st) / 2.0, (w + st) / 2.0
    run = w / 2.0 - hw / 2.0
    y_side = cap - s0 * (cap - yj) / run
    y_crotch = cap - (w / 2.0 - hw) * (cap - yj) / run
    if not (0.0 < y_side < cap and yj < y_crotch < cap):
        raise ValueError("Y arms do not fit this width; widen it or thin the stem")
    base = [
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
    baked = _cap_serif_inlined(ctx)
    if baked and ctx.style.serif == "bracketed":
        return _y_cap_bracketed_outline(h, ctx, base)
    if baked:
        return _polygon(_y_cap_slab_points(h, ctx, base))
    # Sans: seal crotch tip (index 7).
    sealed = _truncate_crotch(base, 7, _crotch_seal_flat(st))
    if _cap_italic_sans(ctx):
        outline = _soft_corner_polygon(sealed, frozenset({1, 4, 7, 8}), h.stem * 0.32)
        return _apply_italic_opening_tip_shear(
            ctx,
            outline,
            ((hw * 0.5, cap), (w - hw * 0.5, cap)),
            stem=h.stem,
        )
    return _polygon(sealed)


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
    w = width * h.width
    baked = _cap_serif_inlined(c)
    anchors = _cap_anchors(
        w,
        h,
        stem_serif_anchors=_cap_stem_serif_anchors_enabled(c, baked=baked, diagonal=True),
    )
    return _pack(c, h, anchors, Y_yoke(c, metrics=h, width=width, junction=junction))


def _m_cap_foot_dims(
    h: HMetrics, ctx: DesignContext, *, w: float, bx: float
) -> tuple[float, float, float]:
    t, cap = h.stem, h.cap_height
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    gap = max(w - 2.0 * t, t)
    l = min(length, t * 0.48, gap * 0.32, max(bx - t, t) * 0.42)
    th = min(thick, cap * 0.1, t * 0.18, gap * 0.14)
    return l, th, bracket_r


def _write_m_bracketed_outer(
    b: PathBuilder,
    h: HMetrics,
    ctx: DesignContext,
    *,
    w: float,
    y_low: float,
    y_v: float,
    bx: float,
) -> None:
    t, cap = h.stem, h.cap_height
    l, th, bracket_r = _m_cap_foot_dims(h, ctx, w=w, bx=bx)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    b.lineTo(t, 0.0)
    b.lineTo(t, y_low)
    b.lineTo(bx, 0.0)
    b.lineTo(w - bx, 0.0)
    b.lineTo(w - t, y_low)
    b.lineTo(w - t, 0.0)
    b.lineTo(w - t - l, -th)
    _finish_baseline_foot_pad(b, w - t - l, w + l, th, bracket_r, bracketed=True)
    b.lineTo(w, 0.0)
    b.lineTo(w, cap)
    b.lineTo(w + l, cap)
    _append_upward_cap_foot_pad(b, w - t - l, w + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(w - t, cap)
    b.lineTo(w / 2.0, y_v)
    b.lineTo(t, cap)
    b.lineTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()


def _m_cap_outline_points(
    h: HMetrics,
    ctx: DesignContext,
    *,
    w: float,
    y_low: float,
    y_v: float,
    bx: float,
) -> list[Pt]:
    t, cap = h.stem, h.cap_height
    if ctx.style.serif != "slab":
        return [
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
    l, th, _ = _m_cap_foot_dims(h, ctx, w=w, bx=bx)
    return [
        (-l, -th),
        (t + l, -th),
        (t + l, 0.0),
        (t, 0.0),
        (t, y_low),
        (bx, 0.0),
        (w - bx, 0.0),
        (w - t, y_low),
        (w - t, 0.0),
        (w - t - l, 0.0),
        (w - t - l, -th),
        (w + l, -th),
        (w + l, 0.0),
        (w, 0.0),
        (w, cap),
        (w + l, cap),
        (w + l, cap + th),
        (w - t - l, cap + th),
        (w - t - l, cap),
        (w - t, cap),
        (w / 2.0, y_v),
        (t, cap),
        (t + l, cap),
        (t + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def M_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 1.18,
    apex: float = 0.35,
) -> Outline:
    """Continuous cap ``M`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    s = ctx.stem
    w_frac = width
    vertex_apex = apex
    if s <= 72.0:
        vertex_apex = 0.38
        if ctx.contrast >= 1.0:
            w_frac += 0.02
    if 100.0 <= s <= 118.0:
        if ctx.contrast >= 1.0:
            vertex_apex = 0.38
            w_frac += 0.012
        else:
            vertex_apex = 0.40
    if 168.0 <= s <= 192.0:
        vertex_apex = max(vertex_apex, 0.38)
    if s >= 198.0:
        w_frac += 0.02
    if ctx.style.serif in ("slab", "bracketed"):
        if s <= 78.0:
            w_frac += 0.06
            if ctx.style.serif == "bracketed" and s <= 72.0:
                w_frac += 0.05
        if 100.0 <= s <= 118.0:
            w_frac += 0.05
        if 138.0 <= s <= 162.0:
            w_frac += 0.04
        if 168.0 <= s <= 192.0:
            w_frac += 0.07 if ctx.style.serif == "bracketed" else 0.05
            vertex_apex = max(vertex_apex, 0.38)
    w, cap, st = w_frac * h.width, h.cap_height, h.stem
    f = vertex_apex * st
    bx = w / 2.0 - f / 2.0
    hw = _hwidth(st, ctx.contrast, bx - st, cap)
    for _ in range(8):
        hw = _hwidth(st, ctx.contrast, bx - st + hw, cap)
    slope = cap / (st - bx - hw)
    y_low = slope * (st - bx)
    y_v = slope * (f / 2.0 - hw)
    if not (0.0 < y_low < cap and 0.0 < y_v < cap and hw > f / 2.0):
        raise ValueError("M strokes do not fit this width; widen it or thin the stem")
    if ctx.style.serif == "bracketed":
        b = PathBuilder()
        _write_m_bracketed_outer(b, h, ctx, w=w, y_low=y_low, y_v=y_v, bx=bx)
        return _ccw(b.build())
    if _cap_italic_sans(ctx):
        return _m_italic_sans_outline(h, ctx, w=w, y_low=y_low, y_v=y_v, bx=bx)
    pts = _m_cap_outline_points(h, ctx, w=w, y_low=y_low, y_v=y_v, bx=bx)
    return _polygon(pts)


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
    if c.style.serif in ("slab", "bracketed"):
        if s <= 78.0:
            w_frac += 0.06
            if c.style.serif == "bracketed" and s <= 72.0:
                w_frac += 0.05
        if 100.0 <= s <= 118.0:
            w_frac += 0.05
        if 138.0 <= s <= 162.0:
            w_frac += 0.04
        if 168.0 <= s <= 192.0:
            w_frac += 0.07 if c.style.serif == "bracketed" else 0.05
            vertex_apex = max(vertex_apex, 0.38)
    w, cap, st = w_frac * h.width, h.cap_height, h.stem
    inlined = c.style.serif in ("slab", "bracketed")
    half = st / 2.0
    anchors: dict[str, Pt] = {
        "top": (w / 2.0, cap),
        "bottom": (w / 2.0, 0.0),
    }
    if _cap_stem_serif_anchors_enabled(c, baked=inlined):
        anchors.update(
            {
                "stem_L_b": (half, 0.0),
                "stem_L_t": (half, cap),
                "stem_R_b": (w - half, 0.0),
                "stem_R_t": (w - half, cap),
            }
        )
    return _pack(c, h, anchors, M_yoke(c, metrics=h, width=width, apex=apex))


def _n_cap_foot_dims(h: HMetrics, ctx: DesignContext, *, w: float) -> tuple[float, float, float]:
    t, cap = h.stem, h.cap_height
    from typekernel.parts.serifs import serif_metrics

    length, thick, bracket_r = serif_metrics(ctx)
    gap = max(w - 2.0 * t, t)
    l = min(length, t * 0.48, gap * 0.32)
    th = min(thick, cap * 0.1, t * 0.18, gap * 0.14)
    return l, th, bracket_r


def _write_n_bracketed_outer(
    b: PathBuilder,
    h: HMetrics,
    ctx: DesignContext,
    *,
    w: float,
    y_left: float,
    y_right: float,
) -> None:
    t, cap = h.stem, h.cap_height
    l, th, bracket_r = _n_cap_foot_dims(h, ctx, w=w)
    b.moveTo(-l, -th)
    _finish_baseline_foot_pad(b, -l, t + l, th, bracket_r, bracketed=True)
    b.lineTo(t, 0.0)
    b.lineTo(t, y_left)
    b.lineTo(w - t, 0.0)
    b.lineTo(w - t - l, -th)
    _finish_baseline_foot_pad(b, w - t - l, w + l, th, bracket_r, bracketed=True)
    b.lineTo(w, 0.0)
    b.lineTo(w, cap)
    b.lineTo(w + l, cap)
    _append_upward_cap_foot_pad(b, w - t - l, w + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(w - t, cap)
    b.lineTo(w - t, y_right)
    b.lineTo(t, cap)
    b.lineTo(t + l, cap)
    _append_upward_cap_foot_pad(b, -l, t + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, 0.0)
    b.lineTo(-l, 0.0)
    b.closePath()


def _n_cap_outline_points(
    h: HMetrics,
    ctx: DesignContext,
    *,
    w: float,
    y_left: float,
    y_right: float,
) -> list[Pt]:
    t, cap = h.stem, h.cap_height
    if ctx.style.serif != "slab":
        return [
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
    l, th, _ = _n_cap_foot_dims(h, ctx, w=w)
    return [
        (-l, -th),
        (t + l, -th),
        (t + l, 0.0),
        (t, 0.0),
        (t, y_left),
        (w - t, 0.0),
        (w - t - l, 0.0),
        (w - t - l, -th),
        (w + l, -th),
        (w + l, 0.0),
        (w, 0.0),
        (w, cap),
        (w + l, cap),
        (w + l, cap + th),
        (w - t - l, cap + th),
        (w - t - l, cap),
        (w - t, cap),
        (w - t, y_right),
        (t, cap),
        (t + l, cap),
        (t + l, cap + th),
        (-l, cap + th),
        (-l, cap),
        (0.0, cap),
        (0.0, 0.0),
        (-l, 0.0),
    ]


def N_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 1.0,
) -> Outline:
    """Continuous cap ``N`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    c = ctx
    s = c.stem
    w_frac = width
    # Mirror N_from_H width adjustments (keep in sync).
    if s <= 72.0:
        w_frac += 0.02
    if 100.0 <= s <= 118.0:
        w_frac += 0.022
    if 168.0 <= s <= 192.0:
        w_frac += 0.035
    if c.style.serif in ("slab", "bracketed"):
        if s <= 78.0:
            w_frac += 0.06
            if c.style.serif == "bracketed" and s <= 72.0:
                w_frac += 0.05
        if 100.0 <= s <= 118.0:
            w_frac += 0.05
        if 138.0 <= s <= 162.0:
            w_frac += 0.04
        if 168.0 <= s <= 192.0:
            w_frac += 0.07 if c.style.serif == "bracketed" else 0.05
        if s >= 198.0:
            w_frac += 0.02
        if c.style.serif == "bracketed" and 175.0 <= s < 198.0:
            w_frac += 0.02
    w, cap, st = w_frac * h.width, h.cap_height, h.stem
    hw = _hwidth(st, c.contrast, w - 2.0 * st, cap)
    for _ in range(8):
        hw = _hwidth(st, c.contrast, w - 2.0 * st + hw, cap)
    slope = cap / (2.0 * st - hw - w)
    y_left = slope * (2.0 * st - w)
    y_right = -slope * hw
    if not (0.0 < y_right < cap and 0.0 < y_left < cap):
        raise ValueError("N diagonal does not fit this width; widen it or thin the stem")
    if c.style.serif == "bracketed":
        b = PathBuilder()
        _write_n_bracketed_outer(b, h, c, w=w, y_left=y_left, y_right=y_right)
        return _ccw(b.build())
    if _cap_italic_sans(c):
        return _n_italic_sans_outline(h, c, w=w, y_left=y_left, y_right=y_right)
    pts = _n_cap_outline_points(h, c, w=w, y_left=y_left, y_right=y_right)
    return _polygon(pts)


def N_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 1.0,
) -> ComposedGlyph:
    """``N``: two ``H`` stems joined by one compensated diagonal."""
    c = ctx or H.context
    h = _h_record(H)
    s = c.stem
    w_frac = width
    if s <= 72.0:
        w_frac += 0.02
    if 100.0 <= s <= 118.0:
        w_frac += 0.022
    if 168.0 <= s <= 192.0:
        w_frac += 0.035
    if c.style.serif in ("slab", "bracketed"):
        if s <= 78.0:
            w_frac += 0.06
            if c.style.serif == "bracketed" and s <= 72.0:
                w_frac += 0.05
        if 100.0 <= s <= 118.0:
            w_frac += 0.05
        if 138.0 <= s <= 162.0:
            w_frac += 0.04
        if 168.0 <= s <= 192.0:
            w_frac += 0.07 if c.style.serif == "bracketed" else 0.05
        if s >= 198.0:
            w_frac += 0.02
        if c.style.serif == "bracketed" and 175.0 <= s < 198.0:
            w_frac += 0.02
    w, cap, st = w_frac * h.width, h.cap_height, h.stem
    inlined = c.style.serif in ("slab", "bracketed")
    half = st / 2.0
    anchors: dict[str, Pt] = {
        "top": (w / 2.0, cap),
        "bottom": (w / 2.0, 0.0),
    }
    if _cap_stem_serif_anchors_enabled(c, baked=inlined):
        anchors.update(
            {
                "stem_L_b": (half, 0.0),
                "stem_L_t": (half, cap),
                "stem_R_b": (w - half, 0.0),
                "stem_R_t": (w - half, cap),
            }
        )
    return _pack(c, h, anchors, N_yoke(c, metrics=h, width=width))


def _t_outline_points(h: HMetrics, ctx: DesignContext, *, width: float) -> list[Pt]:
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    s0, s1 = (w - t) / 2.0, (w + t) / 2.0
    if ctx.style.serif != "slab":
        return [
            (s0, 0.0),
            (s1, 0.0),
            (s1, cap - bt),
            (w, cap - bt),
            (w, cap),
            (0.0, cap),
            (0.0, cap - bt),
            (s0, cap - bt),
        ]
    l, th, _ = _l_cap_foot_dims(h, ctx)
    return [
        (s0 - l, -th),
        (s1 + l, -th),
        (s1 + l, 0.0),
        (s1, 0.0),
        (s1, cap - bt),
        (w, cap - bt),
        (w, cap),
        (s1 + l, cap),
        (s1 + l, cap + th),
        (s0 - l, cap + th),
        (s0 - l, cap),
        (0.0, cap),
        (0.0, cap - bt),
        (s0, cap - bt),
        (s0, 0.0),
        (s0 - l, 0.0),
    ]


def _write_t_bracketed_outer(
    b: PathBuilder, h: HMetrics, ctx: DesignContext, *, width: float
) -> None:
    t, cap, bt = h.stem, h.cap_height, h.bar
    w = width * h.width
    s0, s1 = (w - t) / 2.0, (w + t) / 2.0
    l, th, bracket_r = _l_cap_foot_dims(h, ctx)
    b.moveTo(s0 - l, -th)
    _finish_baseline_foot_pad(b, s0 - l, s1 + l, th, bracket_r, bracketed=True)
    b.lineTo(s1, 0.0)
    b.lineTo(s1, cap - bt)
    b.lineTo(w, cap - bt)
    b.lineTo(w, cap)
    b.lineTo(s1 + l, cap)
    _append_upward_cap_foot_pad(b, s0 - l, s1 + l, cap, th, bracket_r, bracketed=True)
    b.lineTo(0.0, cap)
    b.lineTo(0.0, cap - bt)
    b.lineTo(s0, cap - bt)
    b.lineTo(s0, 0.0)
    b.lineTo(s0 - l, 0.0)
    b.closePath()


def T_yoke(
    ctx: DesignContext,
    *,
    metrics: HMetrics | None = None,
    width: float = 0.92,
    real_flare: bool = False,
) -> Outline:
    """Continuous cap ``T`` body — Usage A."""
    h = metrics or h_cap_metrics(ctx)
    w = width * h.width
    if ctx.style.serif == "bracketed":
        b = PathBuilder()
        _write_t_bracketed_outer(b, h, ctx, width=width)
        return _ccw(b.build())
    if _cap_italic_sans(ctx):
        outline = _t_italic_sans_outline(h, ctx, width=width)
        return _apply_italic_opening_tip_shear(
            ctx,
            outline,
            ((0.0, h.cap_height - h.bar * 0.5), (w, h.cap_height - h.bar * 0.5)),
            stem=h.stem,
        )
    pts = _t_outline_points(h, ctx, width=width)
    if ctx.style.serif == "slab":
        return _polygon(pts)
    return _cap_f_t_outline(
        ctx, pts, w, h.cap_height, h.bar, real_flare=real_flare
    )


def T_from_H(
    H: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float = 0.92,
    real_flare: bool = False,
) -> ComposedGlyph:
    """``T``: an ``H`` stem centred under a top bar ``width`` × the ``H`` width."""
    c = ctx or H.context
    h = _h_record(H)
    w = width * h.width
    inlined = c.style.serif in ("slab", "bracketed")
    cx = w / 2.0
    anchors: dict[str, Pt] = {
        "top": (w / 2.0, h.cap_height),
        "bottom": (cx, 0.0),
    }
    if _cap_stem_serif_anchors_enabled(c, baked=inlined):
        anchors["stem_M_b"] = (cx, 0.0)
        anchors["stem_M_t"] = (cx, h.cap_height)
    return _pack(
        c, h, anchors, T_yoke(c, metrics=h, width=width, real_flare=real_flare)
    )
