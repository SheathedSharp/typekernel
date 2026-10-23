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

from typekernel.geo.outline import Outline, bounds
from typekernel.geo.path_builder import PathBuilder
from typekernel.optics.stem import diagonal_compensation
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.control import _ccw, _n_record, _pack, _vertical_stem_serif_anchors
from typekernel.parts.terminal_openings import apply_terminal_shear

__all__ = [
    "k_from_n",
    "k_points",
    "k_yoke",
    "v_from_n",
    "v_points",
    "v_yoke",
    "w_from_n",
    "w_points",
    "w_yoke",
    "x_from_n",
    "x_points",
    "x_yoke",
    "y_from_n",
    "y_yoke",
    "z_from_n",
    "z_points",
    "z_yoke",
]

Pt = tuple[float, float]


def _polygon(points: list[Pt]) -> Outline:
    b = PathBuilder()
    b.moveTo(*points[0])
    for p in points[1:]:
        b.lineTo(*p)
    b.closePath()
    return _ccw(b.build())


def _italic_diags(ctx: DesignContext) -> bool:
    """True italic / VF-compat diagonal constructions (not shear-only)."""
    from typekernel.parts.control import _italic_topology

    return _italic_topology(ctx)


def _along(from_p: Pt, to_p: Pt, dist: float) -> Pt:
    dx, dy = to_p[0] - from_p[0], to_p[1] - from_p[1]
    length = math.hypot(dx, dy) or 1.0
    t = min(max(dist, 0.0) / length, 0.42)
    return (from_p[0] + dx * t, from_p[1] + dy * t)



def _crotch_seal_flat(stem: float) -> float:
    """Target chord width for a truncated crotch (VF-safe tip flattening)."""
    return max(5.5, stem * 0.10)


def _truncate_crotch(points: list[Pt], idx: int, flat: float) -> list[Pt]:
    """Replace ``points[idx]`` with a two-point flat of chord width ``flat`` (net +1).

    Insets along both edges from the tip so masters keep a fixed topology and
    stay interpolatable. Used to seal even-odd slits at sharp diagonal crotches.
    """
    n = len(points)
    if not 0 <= idx < n:
        raise IndexError(f"crotch index {idx} out of range for {n} points")
    if flat <= 0:
        raise ValueError(f"flat must be positive, got {flat!r}")
    a = points[(idx - 1) % n]
    c = points[idx]
    b = points[(idx + 1) % n]
    va = (a[0] - c[0], a[1] - c[1])
    vb = (b[0] - c[0], b[1] - c[1])
    la = math.hypot(*va) or 1.0
    lb = math.hypot(*vb) or 1.0
    ua = (va[0] / la, va[1] / la)
    ub = (vb[0] / lb, vb[1] / lb)
    dot = max(-1.0, min(1.0, ua[0] * ub[0] + ua[1] * ub[1]))
    sin_half = math.sqrt(max(0.0, 0.5 * (1.0 - dot))) or 1e-6
    t = min(flat / (2.0 * sin_half), 0.45 * la, 0.45 * lb)
    p = (c[0] + ua[0] * t, c[1] + ua[1] * t)
    q = (c[0] + ub[0] * t, c[1] + ub[1] * t)
    return points[:idx] + [p, q] + points[idx + 1 :]


def _seal_crotches(points: list[Pt], indices: tuple[int, ...], flat: float) -> list[Pt]:
    """Truncate several crotches; ``indices`` high-to-low so earlier slots stay stable."""
    out = points
    for idx in sorted(indices, reverse=True):
        out = _truncate_crotch(out, idx, flat)
    return out


def _soft_corner_polygon(points: list[Pt], soft: frozenset[int], radius: float) -> Outline:
    """Closed polygon with listed corners as cubics, then R4 extrema rebalance.

    Cursive italic crotches: tangent cubics at soft indices, then
    :func:`~typekernel.geo.extrema.outline_with_axis_extrema_on_curve` so
    axis turning points land on nodes (R4-safe). Falls back to a line chamfer
    only when ``radius`` is non-positive.
    """
    if radius <= 0.0 or not soft:
        return _polygon(points)
    from typekernel.geo.extrema import outline_with_axis_extrema_on_curve

    n = len(points)
    b = PathBuilder()
    first = True
    for i in range(n):
        prev_p = points[(i - 1) % n]
        cur = points[i]
        nxt = points[(i + 1) % n]
        if i in soft:
            enter = _along(cur, prev_p, radius)
            exit_pt = _along(cur, nxt, radius)
            c1 = (enter[0] * 0.35 + cur[0] * 0.65, enter[1] * 0.35 + cur[1] * 0.65)
            c2 = (exit_pt[0] * 0.35 + cur[0] * 0.65, exit_pt[1] * 0.35 + cur[1] * 0.65)
            if first:
                b.moveTo(*enter)
                first = False
            else:
                b.lineTo(*enter)
            b.curveTo(c1[0], c1[1], c2[0], c2[1], exit_pt[0], exit_pt[1])
        else:
            if first:
                b.moveTo(*cur)
                first = False
            else:
                b.lineTo(*cur)
    b.closePath()
    return outline_with_axis_extrema_on_curve(_ccw(b.build()))



def _diag_stroke_weight(stem: float, *, base: float = 1.0, thin: float = 0.20) -> float:
    """Scale diagonal stroke weight toward black so v/w do not out-ink x/y/k.

    Uses :func:`~typekernel.parts.weight_relief.stem_weight_fraction` only —
    topology (point counts) stays fixed for VF.
    """
    from typekernel.parts.weight_relief import stem_weight_fraction

    return base * (1.0 - thin * stem_weight_fraction(stem))


def _hwidth(stem: float, contrast: float, run: float, rise: float, weight: float = 1.0) -> float:
    """Horizontal width of a diagonal whose centreline runs ``run`` over ``rise``."""
    phi = math.degrees(math.atan2(abs(run), abs(rise)))
    perp = diagonal_compensation(phi, stem * weight, contrast=contrast)
    return perp / math.cos(math.radians(phi))


def _v_geometry(
    stem: float,
    height: float,
    width: float,
    contrast: float,
    apex: float,
    weight: float = 1.0,
) -> tuple[float, float, float, float]:
    """``(a0, hw, crotch_y, tan)`` for a ``v`` of outer ``width``.

    ``a0`` is the left end of the flat apex; ``tan`` the stroke's run per unit
    of descent. Raises if the strokes are too heavy for the width.
    """
    flat = apex * stem
    a0 = (width - flat) / 2.0
    tan = a0 / height
    hw = _hwidth(stem, contrast, a0, height, weight)
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
    seal_crotches: bool = True,
    weight: float = 1.0,
) -> list[Pt]:
    """Two compensated diagonals meeting at a flat apex on the baseline.

    When ``seal_crotches`` (default), the inner crotch tip is truncated to a
    flat of width :func:`_crotch_seal_flat` (7→8 points; VF-safe across masters).
    Visual join quality is vision-reviewed on proofs, not coded as a gate.
    ``weight`` thins strokes toward black (optical match with ``x``/``k``).
    """
    a0, hw, cy, _ = _v_geometry(stem, height, width, contrast, apex, weight)
    w, h = width, height + top_overshoot
    pts = [(0.0, h), (a0, 0.0), (w - a0, 0.0), (w, h), (w - hw, h), (w / 2.0, cy), (hw, h)]
    if seal_crotches:
        pts = _truncate_crotch(pts, 5, _crotch_seal_flat(stem))
    return pts


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
    # Low crotch (3) + two upper notches (8, 11); truncate high→low.
    return _seal_crotches(pts, (3, 8, 11), _crotch_seal_flat(stem))


def x_points(
    stem: float, height: float, width: float, contrast: float, weight: float = 1.0
) -> list[Pt]:
    """Two compensated diagonals crossing at mid height."""
    w, xh = width, height
    hw = stem * weight
    for _ in range(8):
        hw = _hwidth(stem, contrast, w - hw, xh, weight=weight)
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
    # Top and bottom waist crotches of the cross (4, 10).
    return _seal_crotches(pts, (4, 10), _crotch_seal_flat(stem))


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
    weight: float = 1.0,
) -> list[Pt]:
    """Stem to ``stem_top`` with arm (to ``arm_top``) and leg meeting at the stem.

    Arm and leg centrelines meet on the stem's right face at ``vertex`` ×
    ``arm_top``; the arm ends flat at ``arm_top``, the leg on the baseline.
    ``weight`` scales arm/leg stroke (stem stays ``stem`` wide).
    """
    t, w, xh = stem, width, arm_top
    yj = vertex * xh
    hw_a = _hwidth(t, contrast, w - t, xh - yj, weight)
    hw_l = _hwidth(t, contrast, w - t, yj, weight)
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
    # Horizontal shelves at stem↔leg / stem↔arm joins (clears taper hairlines
    # that edge-inset chamfers leave on a vertical stem) + truncated arm/leg crotch.
    shelf = _crotch_seal_flat(stem)
    pts = [
        (0.0, 0.0),
        (t, 0.0),
        (t, y_ll),
        (t + shelf, y_ll),
        (w - hw_l, 0.0),
        (w, 0.0),
        crotch,
        (w, xh),
        (w - hw_a, xh),
        (t + shelf, y_au),
        (t, y_au),
        (t, stem_top),
        (0.0, stem_top),
    ]
    # Crotch tip is index 6 before truncate → flat at 6,7 (13→14 points).
    return _truncate_crotch(pts, 6, shelf)


def v_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    apex: float = 0.35,
    real_flare: bool = False,
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
    # Thin diagonals toward black so v does not optically out-weigh x/y/k.
    dw = _diag_stroke_weight(m.stem, thin=0.22)
    pts = v_points(
        m.stem, m.x_height, w, c.contrast, apex, top_overshoot=bump, weight=dw
    )
    top = m.x_height + bump
    if _italic_diags(c):
        # Asymmetric italic v: bias apex/crotch right; cursive cubic crotch.
        bias = 0.11 * w
        pts = list(pts)
        pts[1] = (pts[1][0] + bias * 0.25, pts[1][1])
        pts[2] = (pts[2][0] + bias * 0.55, pts[2][1])
        pts[5] = (pts[5][0] + bias * 0.45, pts[5][1])
        outline = _soft_corner_polygon(pts, frozenset({5, 6}), m.stem * 0.38)
    else:
        outline = _polygon(pts)
    if real_flare:
        # Outer top corners of the two arms (inward = into the letter).
        min_x, _min_y, max_x, max_y = bounds(outline)
        for tip in ((min_x + m.stem * 0.05, max_y), (max_x - m.stem * 0.05, max_y)):
            outline = apply_terminal_shear(
                c, outline, at=tip, along="y", inward="-", real_flare=True
            )
    return _pack(c, m, {"top": (w / 2.0, top), "bottom": (w / 2.0, 0.0)}, outline)


def y_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    apex: float = 0.35,
    real_flare: bool = False,
) -> ComposedGlyph:
    """``y``: the ``v`` with its right stroke carried straight to the descender."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    apex_eff = apex
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
        if c.style.serif in ("slab", "bracketed"):
            if 100.0 <= s <= 118.0:
                scale += 0.07 if c.style.serif == "slab" else 0.055
                apex_eff = min(apex_eff, 0.33)
            if 138.0 <= s <= 162.0:
                scale += 0.04
            if 168.0 <= s <= 192.0:
                scale += 0.05
                apex_eff = min(apex_eff, 0.33)
            if s >= 198.0:
                scale += 0.04
                apex_eff = min(apex_eff, 0.32)
        from typekernel.parts.weight_relief import stem_weight_fraction as _swf

        scale += 0.04 * _swf(s)
        w = m.width * scale
    xh, desc = m.x_height, c.descender
    dw = _diag_stroke_weight(m.stem, thin=0.18)
    _, hw, cy, tan = _v_geometry(m.stem, xh, w, c.contrast, apex_eff, dw)
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
    tip_y = desc + m.stem * (0.02 if c.terminal_style == "ball" else 0.08)
    tip_x = tail_r + (hw * 0.32 if c.terminal_style == "ball" else 0.0)
    # Truncate the v-crotch tip (straight idx 6; curved idx 8).
    crotch_i = 8 if c.style.y_tail == "curved" else 6
    pts = _truncate_crotch(pts, crotch_i, _crotch_seal_flat(m.stem))
    if _italic_diags(c):
        # Flat occupies crotch_i, crotch_i+1; also round descender join (index 1).
        poly = _soft_corner_polygon(
            pts, frozenset({1, crotch_i, crotch_i + 1}), m.stem * 0.32
        )
    else:
        poly = _polygon(pts)
    if c.terminal_style == "ball" and m.stem <= 45.0:
        outline = poly
    else:
        ball_r = None
        if c.terminal_style == "ball":
            if m.stem <= 90.0:
                ball_r = m.stem * 0.13
            elif m.stem <= 130.0:
                ball_r = m.stem * 0.15
            elif m.stem <= 170.0:
                ball_r = m.stem * 0.17
            else:
                ball_r = m.stem * 0.24
        outline = apply_terminal_shear(
            c, poly, at=(tip_x, tip_y), ball_radius=ball_r, real_flare=real_flare)
    return _pack(c, m, {"top": (w / 2.0, xh)}, outline)


def w_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    apex: float = 0.35,
    peak: float = 0.35,
    weight: float = 0.9,
    real_flare: bool = False,
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
        from typekernel.parts.weight_relief import stem_weight_fraction as _swf

        scale -= 0.06 * _swf(s)  # rein in optical size vs x/y/k
        ww = m.width * scale
    bump = c.sharp_overshoot
    dw = _diag_stroke_weight(m.stem, base=weight, thin=0.24)
    pts = w_points(
        m.stem,
        m.x_height,
        ww,
        c.contrast,
        apex=apex,
        peak=peak,
        weight=dw,
        top_overshoot=bump,
    )
    anchors = {"top": (ww / 2.0, m.x_height), "bottom": (ww / 2.0, 0.0)}
    if _italic_diags(c):
        # Sealed flats: low crotch 3–4, upper notches 8–9 and 11–12.
        outline = _soft_corner_polygon(
            pts, frozenset({3, 4, 8, 9, 11, 12}), m.stem * 0.28
        )
    else:
        outline = _polygon(pts)
    if real_flare:
        min_x, _min_y, max_x, max_y = bounds(outline)
        for tip in ((min_x + m.stem * 0.05, max_y), (max_x - m.stem * 0.05, max_y)):
            outline = apply_terminal_shear(
                c, outline, at=tip, along="y", inward="-", real_flare=True
            )
    return _pack(c, m, anchors, outline)


def x_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    real_flare: bool = False,
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
        from typekernel.parts.weight_relief import stem_weight_fraction as _swf

        scale += 0.055 * _swf(s)  # optical size vs heavy v/w
        w = m.width * scale
    # Keep x stroke near upright stem; slight heavy-stem fatten vs over-thin v.
    xw = _diag_stroke_weight(m.stem, thin=0.06)
    pts = x_points(m.stem, m.x_height, w, c.contrast, weight=xw)
    if _italic_diags(c):
        # Classic italic x: raise the crossing; round the waist notches.
        dy = 0.07 * m.x_height
        pts = list(pts)
        # Indices 1 and 7 are the mid-waist tips on each diagonal.
        pts[1] = (pts[1][0], pts[1][1] + dy)
        pts[7] = (pts[7][0], pts[7][1] + dy)
        pts[4] = (pts[4][0], pts[4][1] + dy * 0.5)
        pts[10] = (pts[10][0], pts[10][1] + dy * 0.5)
        outline = _soft_corner_polygon(pts, frozenset({1, 4, 5, 8, 10, 11}), m.stem * 0.22)
    else:
        outline = _polygon(pts)
    if real_flare:
        min_x, min_y, max_x, max_y = bounds(outline)
        for tip in (
            (min_x + m.stem * 0.05, max_y),
            (max_x - m.stem * 0.05, max_y),
            (min_x + m.stem * 0.05, min_y),
            (max_x - m.stem * 0.05, min_y),
        ):
            outline = apply_terminal_shear(
                c, outline, at=tip, along="y", inward="auto", real_flare=True
            )
    return _pack(c, m, {"top": (w / 2.0, m.x_height), "bottom": (w / 2.0, 0.0)}, outline)


def z_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    real_flare: bool = False,
) -> ComposedGlyph:
    """``z``: top and bottom bars (thin strokes) joined by one compensated diagonal."""
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    w = 0.88 * m.width if width is None else width
    pts = z_points(m.stem, m.stem * c.contrast * 0.95, m.x_height, w, c.contrast)
    if _italic_diags(c):
        # Round bar↔diagonal joins (indices 3 and 8 in z_points).
        outline = _soft_corner_polygon(pts, frozenset({3, 8}), m.stem * 0.30)
    else:
        outline = _polygon(pts)
    if real_flare:
        min_x, min_y, max_x, max_y = bounds(outline)
        # Top-right and bottom-left bar ends (open stroke tips on z).
        for tip in ((max_x - m.stem * 0.08, max_y), (min_x + m.stem * 0.08, min_y)):
            outline = apply_terminal_shear(
                c, outline, at=tip, along="y", inward="auto", real_flare=True
            )
    return _pack(c, m, {"top": (w / 2.0, m.x_height), "bottom": (w / 2.0, 0.0)}, outline)


def k_from_n(
    n_glyph: ComposedGlyph,
    ctx: DesignContext | None = None,
    *,
    width: float | None = None,
    vertex: float = 0.42,
    real_flare: bool = False,
) -> ComposedGlyph:
    """``k``: the ascending ``n`` stem with arm and leg meeting at the stem.

    Arm and leg centrelines meet on the stem's right face at ``vertex`` ×
    x-height; the arm ends flat at x-height, the leg on the baseline.
    """
    c = ctx or n_glyph.context
    m = _n_record(n_glyph)
    w = 0.9 * m.width if width is None else width
    vertex_eff = vertex
    if width is None:
        s, scale = c.stem, 0.9
        if s <= 72.0:
            scale += 0.07
        elif s < 80.0:
            scale += 0.07 * max(0.0, (80.0 - s) / 50.0)
        if s <= 50.0:
            scale += 0.32
            vertex_eff = max(vertex_eff, 0.44)
        if 65.0 <= s <= 75.0:
            scale += 0.028
            if c.aperture >= 0.68:
                scale += 0.065
            if c.contrast >= 1.0 and c.roundness < 0.26:
                scale += 0.04
        if 100.0 <= s <= 118.0:
            scale += 0.062
            vertex_eff = max(vertex_eff, 0.44)
        if 142.0 <= s <= 158.0:
            scale += 0.036
        if 168.0 <= s <= 192.0:
            scale += 0.042
        if s >= 175.0:
            scale += 0.02
        if s >= 198.0:
            scale += 0.012
        if c.style.serif in ("slab", "bracketed"):
            if 65.0 <= s <= 78.0:
                scale += 0.045
            if 138.0 <= s <= 162.0:
                scale += 0.055 if c.style.serif == "bracketed" else 0.045
            if 100.0 <= s <= 118.0:
                scale += 0.035
        from typekernel.parts.weight_relief import stem_weight_fraction as _swf

        scale += 0.045 * _swf(s)
        w = m.width * scale
    if c.terminal_style in ("angled", "flared", "ball") and width is None:
        w *= 1.026
        if m.stem <= 75.0:
            w *= 1.004
        if c.terminal_style == "ball":
            w *= 1.012
        if c.terminal_style == "flared":
            if m.stem <= 40.0:
                w *= 1.118
                if c.aperture >= 0.62:
                    w *= 1.042
            elif m.stem <= 80.0:
                w *= 1.028
            if 65.0 <= m.stem <= 75.0:
                w *= 1.032
            if 140.0 <= m.stem <= 160.0:
                w *= 1.02
        if c.terminal_style == "ball":
            if 100.0 <= m.stem <= 120.0:
                w *= 1.028
            if 140.0 <= m.stem <= 160.0:
                w *= 1.016
    if _italic_diags(c):
        # Branch arm/leg join higher (closer to italic shoulder language).
        vertex_eff = min(0.58, max(vertex_eff, 0.50))
    # Fatten arm/leg slightly toward black so k matches heavy v/w optical weight.
    kw = _diag_stroke_weight(m.stem, thin=-0.10)
    pts = k_points(m.stem, m.ascender, m.x_height, w, c.contrast, vertex_eff, kw)
    half = m.stem / 2.0
    anchors = {
        "top": (half, m.ascender),
        "bottom": (w / 2.0, 0.0),
        **_vertical_stem_serif_anchors(
            m.stem, half, bottom=0.0, top=m.ascender, side="L", include_top=False
        ),
    }
    tip = (w - m.stem * 0.15, m.x_height * 0.08)
    if _italic_diags(c):
        # Shelves at 2–3 / 10–11; crotch flat at 6–7.
        base_poly = _soft_corner_polygon(
            pts, frozenset({2, 3, 6, 7, 10, 11}), m.stem * 0.34
        )
    else:
        base_poly = _polygon(pts)
    if c.terminal_style == "angled":
        outline = apply_terminal_shear(
            c,
            base_poly,
            at=(w - m.stem * 0.20, m.x_height * 0.09),
            along="x",
            inward="+",
            band=m.stem * 0.26, real_flare=real_flare)
    elif c.terminal_style == "flared":
        if m.stem <= 45.0:
            outline = base_poly
        else:
            outline = apply_terminal_shear(
                c,
                base_poly,
                at=(w - m.stem * 0.20, m.x_height * 0.09),
                along="x",
                inward="+",
                band=m.stem * 0.30, real_flare=real_flare)
    elif c.terminal_style == "ball":
        outline = apply_terminal_shear(
            c, base_poly, at=tip, ball_radius=m.stem * 0.28, real_flare=real_flare)
    else:
        # Arm tip is low on the letter; flare across +x (same axis as stock flared k).
        outline = apply_terminal_shear(
            c,
            base_poly,
            at=tip,
            along="x",
            inward="+",
            real_flare=real_flare,
        )
    return _pack(c, m, anchors, outline)

def v_yoke(
    ctx: DesignContext,
    *,
    width: float | None = None,
    apex: float = 0.35,
    real_flare: bool = False,
) -> Outline:
    """``v`` body polygon — Usage A export of :func:`v_from_n`."""
    from typekernel.parts.control import build_n

    return v_from_n(build_n(ctx), ctx, width=width, apex=apex, real_flare=real_flare).solids[0]


def y_yoke(
    ctx: DesignContext,
    *,
    width: float | None = None,
    apex: float = 0.35,
    real_flare: bool = False,
) -> Outline:
    """``y`` body polygon — Usage A export of :func:`y_from_n`."""
    from typekernel.parts.control import build_n

    return y_from_n(build_n(ctx), ctx, width=width, apex=apex, real_flare=real_flare).solids[0]


def w_yoke(
    ctx: DesignContext,
    *,
    width: float | None = None,
    real_flare: bool = False,
) -> Outline:
    """``w`` body polygon — Usage A export of :func:`w_from_n`."""
    from typekernel.parts.control import build_n

    return w_from_n(build_n(ctx), ctx, width=width, real_flare=real_flare).solids[0]


def x_yoke(
    ctx: DesignContext,
    *,
    width: float | None = None,
    real_flare: bool = False,
) -> Outline:
    """``x`` body polygon — Usage A export of :func:`x_from_n`."""
    from typekernel.parts.control import build_n

    return x_from_n(build_n(ctx), ctx, width=width, real_flare=real_flare).solids[0]


def z_yoke(
    ctx: DesignContext,
    *,
    width: float | None = None,
    real_flare: bool = False,
) -> Outline:
    """``z`` body polygon — Usage A export of :func:`z_from_n`."""
    from typekernel.parts.control import build_n

    return z_from_n(build_n(ctx), ctx, width=width, real_flare=real_flare).solids[0]


def k_yoke(
    ctx: DesignContext,
    *,
    width: float | None = None,
    vertex: float = 0.42,
    real_flare: bool = False,
) -> Outline:
    """``k`` body polygon — Usage A export of :func:`k_from_n`."""
    from typekernel.parts.control import build_n

    return k_from_n(
        build_n(ctx), ctx, width=width, vertex=vertex, real_flare=real_flare
    ).solids[0]

