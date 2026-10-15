"""Diagonal letters — ``v w y x z k`` (and the capitals' ``V W X Z K``).

Straight-sided letters drawn as closed polygons with a fixed point count, so
masters interpolate. Stroke weight comes from the stem through
:func:`~typekernel.optics.stem.diagonal_compensation`: a diagonal's
perpendicular thickness is thinned so it reads as heavy as the upright stem;
its *horizontal* width is that thickness divided by ``cos(angle)``.

The ``*_points`` functions are the geometry in plain numbers (stem, height,
width); the ``*_from_n`` wrappers feed them the ``n`` record, and
:mod:`typekernel.parts.caps` feeds them the ``H`` record at cap height.
"""

from __future__ import annotations

import math

from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.optics.stem import diagonal_compensation
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import _ccw, _n_record, _pack
from typekernel.parts.terminal_openings import apply_terminal_shear

__all__ = [
    "k_from_n",
    "k_points",
    "v_from_n",
    "v_points",
    "w_from_n",
    "w_points",
    "x_from_n",
    "x_points",
    "y_from_n",
    "z_from_n",
    "z_points",
]

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
    stem: float, height: float, width: float, contrast: float, apex: float
) -> tuple[float, float, float, float]:
    """``(a0, hw, crotch_y, tan)`` for a ``v`` of outer ``width``.

    ``a0`` is the left end of the flat apex; ``tan`` the stroke's run per unit
    of descent. Raises if the strokes are too heavy for the width.
    """
    flat = apex * stem
    a0 = (width - flat) / 2.0
    tan = a0 / height
    hw = _hwidth(stem, contrast, a0, height)
    if hw <= flat / 2.0 or hw >= width / 2.0:
        raise ValueError("diagonal strokes do not fit this width; widen it or thin the stem")
    crotch_y = height * (1.0 - (width / 2.0 - hw) / a0)
    return a0, hw, crotch_y, tan


def v_points(
    stem: float,
    height: float,
    width: float,
    contrast: float,
    apex: float = 0.35,
    *,
    top_overshoot: float = 0.0,
) -> list[Pt]:
    """Two compensated diagonals meeting at a flat apex on the baseline."""
    a0, hw, cy, _ = _v_geometry(stem, height, width, contrast, apex)
    w, h = width, height + top_overshoot
    return [(0.0, h), (a0, 0.0), (w - a0, 0.0), (w, h), (w - hw, h), (w / 2.0, cy), (hw, h)]


def w_points(
    stem: float,
    height: float,
    width: float,
    contrast: float,
    *,
    apex: float = 0.35,
    peak: float = 0.35,
    weight: float = 0.9,
    top_overshoot: float = 0.0,
) -> list[Pt]:
    """Four lighter diagonals; the middle peak reaches ``height``.

    Very heavy weights thin the strokes further (down to 0.4) until they fit.
    """
    ww, xh = width, height + top_overshoot
    f, fm = apex * stem, peak * stem
    geom_h = height
    m_l = (ww - fm) / 2.0
    while True:
        # solve tan with hw depending on the angle (fixed point converges fast)
        hw = stem
        for _ in range(8):
            tan = (m_l - f + hw) / (2.0 * geom_h)
            hw = _hwidth(stem, contrast, tan * geom_h, geom_h, weight)
        a1l = geom_h * tan
        a1r = a1l + f
        low_y = (ww / 2.0 - a1r) / tan
        up_y = (2.0 * hw - f) / (2.0 * tan)
        up_x = a1r - hw + up_y * tan
        if 0.0 < up_y < low_y < geom_h:
            break
        if weight <= 0.4:
            raise ValueError("w strokes do not fit this width; widen it or thin the stem")
        weight = max(0.4, weight * 0.92)
    return [
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


def x_points(stem: float, height: float, width: float, contrast: float) -> list[Pt]:
    """Two compensated diagonals crossing at mid height."""
    w, xh = width, height
    hw = stem
    for _ in range(8):
        hw = _hwidth(stem, contrast, w - hw, xh)
    if not 0.0 < 2.0 * hw < w:
        raise ValueError("x strokes do not fit this width; widen it or thin the stem")
    run = w - hw
    bottom_y = xh * (w - 2.0 * hw) / (2.0 * run)
    top_y = xh * w / (2.0 * run)
    return [
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


def z_points(stem: float, bar: float, height: float, width: float, contrast: float) -> list[Pt]:
    """Top and bottom bars ``bar`` thick joined by one compensated diagonal."""
    w, xh, tb = width, height, bar
    hw = stem
    for _ in range(8):
        hw = _hwidth(stem, contrast, w - hw, xh - 2.0 * tb)
    if not (0.0 < hw < w and 2.0 * tb < xh):
        raise ValueError("z strokes do not fit this width; widen it or thin the stem")
    return [
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


def _intersect(p1: Pt, p2: Pt, p3: Pt, p4: Pt) -> Pt:
    d = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
    a = p1[0] * p2[1] - p1[1] * p2[0]
    b = p3[0] * p4[1] - p3[1] * p4[0]
    return (
        (a * (p3[0] - p4[0]) - (p1[0] - p2[0]) * b) / d,
        (a * (p3[1] - p4[1]) - (p1[1] - p2[1]) * b) / d,
    )


def k_points(
    stem: float,
    stem_top: float,
    arm_top: float,
    width: float,
    contrast: float,
    vertex: float = 0.42,
) -> list[Pt]:
    """Stem to ``stem_top`` with arm (to ``arm_top``) and leg meeting at the stem.

    Arm and leg centrelines meet on the stem's right face at ``vertex`` ×
    ``arm_top``; the arm ends flat at ``arm_top``, the leg on the baseline.
    """
    t, w, xh = stem, width, arm_top
    yj = vertex * xh
    hw_a = _hwidth(t, contrast, w - t, xh - yj)
    hw_l = _hwidth(t, contrast, w - t, yj)
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
    return [
        (0.0, 0.0),
        (t, 0.0),
        (t, y_ll),
        (w - hw_l, 0.0),
        (w, 0.0),
        crotch,
        (w, xh),
        (w - hw_a, xh),
        (t, y_au),
        (t, stem_top),
        (0.0, stem_top),
    ]


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
    if width is None:
        s, scale = c.stem, 1.0
        if s <= 72.0 and (
            0.95 <= c.contrast < 1.0
            or (c.contrast >= 1.0 and c.roundness < 0.26)
        ):
            scale += 0.02
        if s <= 72.0 and c.contrast >= 1.0 and c.roundness >= 0.26:
            scale += 0.032
        if 65.0 <= s <= 75.0:
            scale += 0.085
            if c.aperture >= 0.68:
                scale += 0.045
            if c.contrast >= 1.0 and c.roundness < 0.26:
                scale += 0.062
        if 100.0 <= s <= 118.0:
            scale += 0.022
        if 142.0 <= s <= 158.0:
            scale += 0.052
        if 168.0 <= s <= 192.0:
            scale += 0.022
        if s >= 198.0:
            scale += 0.018
        w = m.width * scale
    bump = c.sharp_overshoot
    pts = v_points(m.stem, m.x_height, w, c.contrast, apex, top_overshoot=bump)
    top = m.x_height + bump
    return _pack(c, m, {"top": (w / 2.0, top), "bottom": (w / 2.0, 0.0)}, _polygon(pts))


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
    if width is None:
        s, scale = c.stem, 1.0
        if s <= 50.0:
            scale += 0.08
            if c.contrast >= 1.0:
                scale += 0.06
        elif s <= 72.0:
            scale += 0.06
        if 65.0 <= s <= 75.0:
            scale += 0.038
            if c.contrast >= 1.0:
                scale += 0.085
        if 100.0 <= s <= 118.0:
            scale += 0.072
            if c.contrast >= 1.0:
                scale += 0.032
        if 142.0 <= s <= 158.0:
            scale += 0.048
        w = m.width * scale
    xh, desc = m.x_height, c.descender
    _, hw, cy, tan = _v_geometry(m.stem, xh, w, c.contrast, apex)
    # left outer edge x = (xh - y)·tan meets the right stroke's left edge
    # x = w - hw - (xh - y)·tan
    join_y = xh - (w - hw) / (2.0 * tan)
    join_x = (xh - join_y) * tan
    tail_r = w - (xh - desc) * tan
    if c.style.y_tail == "curved":
        bulge = w * 0.09
        mid_y = (join_y + desc) / 2.0
        pts = [
            (0.0, xh),
            (join_x, join_y),
            (tail_r - hw * 0.45 + bulge, mid_y),
            (tail_r - hw, desc),
            (tail_r, desc),
            (tail_r + bulge * 0.35, mid_y),
            (w, xh),
            (w - hw, xh),
            (w / 2.0, cy),
            (hw, xh),
        ]
    else:
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
    outline = apply_terminal_shear(c, _polygon(pts), at=(tail_r, desc + m.stem * 0.08))
    return _pack(c, m, {"top": (w / 2.0, xh)}, outline)


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
    if width is None:
        s, scale = c.stem, 1.4
        if s <= 72.0:
            if c.contrast < 0.85:
                scale += 0.02
            else:
                scale += 0.03
        if 65.0 <= s <= 75.0:
            scale += 0.085
            if c.aperture >= 0.68:
                scale += 0.042
            if 0.86 <= c.contrast <= 0.94:
                scale += 0.095
            if c.contrast >= 1.0 and c.roundness < 0.26:
                scale += 0.055
            if c.contrast >= 1.0:
                scale += 0.078
        if 100.0 <= s <= 118.0:
            scale += 0.028
        if 142.0 <= s <= 158.0:
            scale += 0.056
        if 168.0 <= s <= 192.0:
            scale += 0.03
        if s >= 198.0:
            scale += 0.02
        ww = m.width * scale
    bump = c.sharp_overshoot
    pts = w_points(
        m.stem,
        m.x_height,
        ww,
        c.contrast,
        apex=apex,
        peak=peak,
        weight=weight,
        top_overshoot=bump,
    )
    anchors = {"top": (ww / 2.0, m.x_height), "bottom": (ww / 2.0, 0.0)}
    return _pack(c, m, anchors, _polygon(pts))


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
    if width is None:
        s, scale = c.stem, 0.95
        if 100.0 <= s <= 118.0:
            scale += 0.014
        if 65.0 <= s <= 75.0:
            scale += 0.078
            if c.aperture >= 0.68:
                scale += 0.038
            if c.contrast >= 1.0 and c.roundness < 0.26:
                scale += 0.062
        if 142.0 <= s <= 158.0:
            scale += 0.026
        if s >= 168.0:
            scale += 0.022
        w = m.width * scale
    pts = x_points(m.stem, m.x_height, w, c.contrast)
    return _pack(c, m, {"top": (w / 2.0, m.x_height), "bottom": (w / 2.0, 0.0)}, _polygon(pts))


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
    pts = z_points(m.stem, m.stem * c.contrast * 0.95, m.x_height, w, c.contrast)
    return _pack(c, m, {"top": (w / 2.0, m.x_height), "bottom": (w / 2.0, 0.0)}, _polygon(pts))


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
    pts = k_points(m.stem, m.ascender, m.x_height, w, c.contrast, vertex)
    anchors = {"top": (m.stem / 2.0, m.ascender), "bottom": (w / 2.0, 0.0)}
    outline = apply_terminal_shear(c, _polygon(pts), at=(w - m.stem * 0.15, m.x_height * 0.08))
    return _pack(c, m, anchors, outline)
