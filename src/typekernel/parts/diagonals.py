"""Diagonal lowercase — ``v w y x z k`` from the ``n`` design record.

Straight-sided letters drawn as closed polygons with a fixed point count, so
masters interpolate. Stroke weight comes from the ``n`` stem through
:func:`~typekernel.optics.stem.diagonal_compensation`: a diagonal's
perpendicular thickness is thinned so it reads as heavy as the upright stem;
its *horizontal* width is that thickness divided by ``cos(angle)``.
"""

from __future__ import annotations

import math

from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.optics.stem import diagonal_compensation
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import NMetrics, _ccw, _n_record, _pack

__all__ = ["k_from_n", "v_from_n", "w_from_n", "x_from_n", "y_from_n", "z_from_n"]

Pt = tuple[float, float]


def _polygon(points: list[Pt]) -> Outline:
    b = PathBuilder()
    b.moveTo(*points[0])
    for p in points[1:]:
        b.lineTo(*p)
    b.closePath()
    return _ccw(b.build())


def _hwidth(stem: float, contrast: float, run: float, rise: float, weight: float = 1.0) -> float:
    """Horizontal width of a diagonal whose centreline runs ``run`` over ``rise``."""
    phi = math.degrees(math.atan2(abs(run), abs(rise)))
    perp = diagonal_compensation(phi, stem * weight, contrast=contrast)
    return perp / math.cos(math.radians(phi))


def _v_geometry(
    m: NMetrics, c: DesignContext, width: float, apex: float, weight: float = 1.0
) -> tuple[float, float, float, float]:
    """``(a0, hw, crotch_y, tan)`` for a ``v`` of outer ``width``.

    ``a0`` is the left end of the flat apex; ``tan`` the stroke's run per unit
    of descent. Raises if the strokes are too heavy for the width.
    """
    xh = m.x_height
    flat = apex * m.stem
    a0 = (width - flat) / 2.0
    tan = a0 / xh
    hw = _hwidth(m.stem, c.contrast, a0, xh, weight)
    if hw <= flat / 2.0 or hw >= width / 2.0:
        raise ValueError("diagonal strokes do not fit this width; widen it or thin the stem")
    crotch_y = xh * (1.0 - (width / 2.0 - hw) / a0)
    return a0, hw, crotch_y, tan


def v_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    apex: float = 0.35,
) -> ComposedGlyph:
    """``v``: two compensated diagonals meeting at a flat apex on the baseline.

    ``width`` defaults to the ``n``'s ink width; ``apex`` is the flat bottom
    as a fraction of the stem.
    """
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    w = m.width if width is None else width
    xh = m.x_height
    a0, hw, cy, _ = _v_geometry(m, c, w, apex)
    pts = [(0.0, xh), (a0, 0.0), (w - a0, 0.0), (w, xh), (w - hw, xh), (w / 2.0, cy), (hw, xh)]
    return _pack(c, m, {"top": (w / 2.0, xh), "bottom": (w / 2.0, 0.0)}, _polygon(pts))


def y_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    apex: float = 0.35,
) -> ComposedGlyph:
    """``y``: the ``v`` with its right stroke carried straight to the descender."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    w = m.width if width is None else width
    xh, desc = m.x_height, c.descender
    _, hw, cy, tan = _v_geometry(m, c, w, apex)
    # left outer edge x = (xh - y)·tan meets the right stroke's left edge
    # x = w - hw - (xh - y)·tan
    join_y = xh - (w - hw) / (2.0 * tan)
    join_x = (xh - join_y) * tan
    tail_r = w - (xh - desc) * tan
    pts = [
        (0.0, xh),
        (join_x, join_y),
        (tail_r - hw, desc),
        (tail_r, desc),
        (w, xh),
        (w - hw, xh),
        (w / 2.0, cy),
        (hw, xh),
    ]
    return _pack(c, m, {"top": (w / 2.0, xh)}, _polygon(pts))


def w_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    apex: float = 0.35,
    peak: float = 0.35,
    weight: float = 0.9,
) -> ComposedGlyph:
    """``w``: four lighter diagonals; the middle peak reaches x-height.

    ``width`` defaults to 1.4 × the ``n``; ``apex`` / ``peak`` are the flat
    bottom and top as fractions of the stem; ``weight`` thins the strokes
    (four diagonals would otherwise darken the letter).
    """
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    ww = 1.4 * m.width if width is None else width
    xh = m.x_height
    f, fm = apex * m.stem, peak * m.stem
    m_l = (ww - fm) / 2.0
    # Very heavy weights thin the four strokes further until they fit.
    while True:
        # solve tan with hw depending on the angle (fixed point converges fast)
        hw = m.stem
        for _ in range(8):
            tan = (m_l - f + hw) / (2.0 * xh)
            hw = _hwidth(m.stem, c.contrast, tan * xh, xh, weight)
        a1l = xh * tan
        a1r = a1l + f
        low_y = (ww / 2.0 - a1r) / tan
        up_y = (2.0 * hw - f) / (2.0 * tan)
        up_x = a1r - hw + up_y * tan
        if 0.0 < up_y < low_y < xh:
            break
        if weight <= 0.4:
            raise ValueError("w strokes do not fit this width; widen it or thin the stem")
        weight = max(0.4, weight * 0.92)
    pts = [
        (0.0, xh),
        (a1l, 0.0),
        (a1r, 0.0),
        (ww / 2.0, low_y),
        (ww - a1r, 0.0),
        (ww - a1l, 0.0),
        (ww, xh),
        (ww - hw, xh),
        (ww - up_x, up_y),
        (ww - m_l, xh),
        (m_l, xh),
        (up_x, up_y),
        (hw, xh),
    ]
    return _pack(c, m, {"top": (ww / 2.0, xh), "bottom": (ww / 2.0, 0.0)}, _polygon(pts))


def x_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
) -> ComposedGlyph:
    """``x``: two compensated diagonals crossing at mid x-height."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    w = 0.95 * m.width if width is None else width
    xh = m.x_height
    hw = m.stem
    for _ in range(8):
        hw = _hwidth(m.stem, c.contrast, w - hw, xh)
    if not 0.0 < 2.0 * hw < w:
        raise ValueError("x strokes do not fit this width; widen it or thin the stem")
    run = w - hw
    bottom_y = xh * (w - 2.0 * hw) / (2.0 * run)
    top_y = xh * w / (2.0 * run)
    pts = [
        (0.0, xh),
        (run / 2.0, xh / 2.0),
        (0.0, 0.0),
        (hw, 0.0),
        (w / 2.0, bottom_y),
        (w - hw, 0.0),
        (w, 0.0),
        (hw + run / 2.0, xh / 2.0),
        (w, xh),
        (w - hw, xh),
        (w / 2.0, top_y),
        (hw, xh),
    ]
    return _pack(c, m, {"top": (w / 2.0, xh), "bottom": (w / 2.0, 0.0)}, _polygon(pts))


def z_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
) -> ComposedGlyph:
    """``z``: top and bottom bars (thin strokes) joined by one compensated diagonal."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    w = 0.88 * m.width if width is None else width
    xh = m.x_height
    tb = m.stem * c.contrast * 0.95
    hw = m.stem
    for _ in range(8):
        hw = _hwidth(m.stem, c.contrast, w - hw, xh - 2.0 * tb)
    if not (0.0 < hw < w and 2.0 * tb < xh):
        raise ValueError("z strokes do not fit this width; widen it or thin the stem")
    pts = [
        (0.0, 0.0),
        (w, 0.0),
        (w, tb),
        (hw, tb),
        (w, xh - tb),
        (w, xh),
        (0.0, xh),
        (0.0, xh - tb),
        (w - hw, xh - tb),
        (0.0, tb),
    ]
    return _pack(c, m, {"top": (w / 2.0, xh), "bottom": (w / 2.0, 0.0)}, _polygon(pts))


def _line_x(p: Pt, q: Pt, y: float) -> float:
    return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])


def _intersect(p1: Pt, p2: Pt, p3: Pt, p4: Pt) -> Pt:
    d = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
    a = p1[0] * p2[1] - p1[1] * p2[0]
    b = p3[0] * p4[1] - p3[1] * p4[0]
    return (
        (a * (p3[0] - p4[0]) - (p1[0] - p2[0]) * b) / d,
        (a * (p3[1] - p4[1]) - (p1[1] - p2[1]) * b) / d,
    )


def k_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    vertex: float = 0.42,
) -> ComposedGlyph:
    """``k``: the ascending ``n`` stem with arm and leg meeting at the stem.

    Arm and leg centrelines meet on the stem's right face at ``vertex`` ×
    x-height; the arm ends flat at x-height, the leg on the baseline.
    """
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    w = 0.9 * m.width if width is None else width
    t, xh, asc = m.stem, m.x_height, m.ascender
    yj = vertex * xh
    hw_a = _hwidth(t, c.contrast, w - t, xh - yj)
    hw_l = _hwidth(t, c.contrast, w - t, yj)
    # arm: flat top [w-hw_a, w] at x-height; leg: flat foot [w-hw_l, w] on baseline
    arm_c = (w - hw_a / 2.0, xh)
    leg_c = (w - hw_l / 2.0, 0.0)
    v = (t, yj)
    arm_up = ((w - hw_a, xh), (w - hw_a - (arm_c[0] - v[0]), yj))
    arm_lo = ((w, xh), (w - (arm_c[0] - v[0]), yj))
    leg_lo = ((w - hw_l, 0.0), (w - hw_l - (leg_c[0] - v[0]), yj))
    leg_up = ((w, 0.0), (w - (leg_c[0] - v[0]), yj))
    y_au = arm_up[0][1] + (t - arm_up[0][0]) * (arm_up[1][1] - arm_up[0][1]) / (
        arm_up[1][0] - arm_up[0][0]
    )
    y_ll = leg_lo[0][1] + (t - leg_lo[0][0]) * (leg_lo[1][1] - leg_lo[0][1]) / (
        leg_lo[1][0] - leg_lo[0][0]
    )
    crotch = _intersect(*arm_lo, *leg_up)
    if not (0.0 < y_ll < y_au < xh and crotch[0] > t):
        raise ValueError("k strokes do not fit this width; widen it or thin the stem")
    pts = [
        (0.0, 0.0),
        (t, 0.0),
        (t, y_ll),
        (w - hw_l, 0.0),
        (w, 0.0),
        crotch,
        (w, xh),
        (w - hw_a, xh),
        (t, y_au),
        (t, asc),
        (0.0, asc),
    ]
    anchors = {"top": (t / 2.0, asc), "bottom": (w / 2.0, 0.0)}
    return _pack(c, m, anchors, _polygon(pts))
