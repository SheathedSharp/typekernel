"""Reusable glyph parts — the Mesh / geometry primitives of type design.

Each factory returns a cubic :class:`~typekernel.geo.outline.Outline` sized from
a shared :class:`~typekernel.parts.context.DesignContext`, so composing letters
is closer to assembling Three.js meshes than redrawing Béziers per glyph.
"""

from __future__ import annotations

import math

from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.path_helpers import KAPPA
from typekernel.parts.context import DesignContext


def vertical_stem(
    ctx: DesignContext,
    x_left: float,
    y_bottom: float,
    y_top: float,
    *,
    width: float | None = None,
) -> Outline:
    """Axis-aligned vertical stem rectangle."""
    w = ctx.stem if width is None else width
    return _rect(x_left, y_bottom, x_left + w, y_top)


def horizontal_bar(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_bottom: float,
    *,
    thickness: float | None = None,
) -> Outline:
    """Axis-aligned horizontal bar."""
    t = ctx.thin if thickness is None else thickness
    return _rect(x_left, y_bottom, x_right, y_bottom + t)


def rounded_rect(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    radius: float | None = None,
) -> Outline:
    """Rectangle with optional corner fillets from ``ctx.roundness``."""
    r = ctx.join_radius if radius is None else radius
    if r <= 0:
        return _rect(x0, y0, x1, y1)
    r = min(r, abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0)
    b = PathBuilder()
    b.moveTo(x0 + r, y0)
    b.lineTo(x1 - r, y0)
    b.curveTo(x1 - r + r * KAPPA, y0, x1, y0 + r - r * KAPPA, x1, y0 + r)
    b.lineTo(x1, y1 - r)
    b.curveTo(x1, y1 - r + r * KAPPA, x1 - r + r * KAPPA, y1, x1 - r, y1)
    b.lineTo(x0 + r, y1)
    b.curveTo(x0 + r - r * KAPPA, y1, x0, y1 - r + r * KAPPA, x0, y1 - r)
    b.lineTo(x0, y0 + r)
    b.curveTo(x0, y0 + r - r * KAPPA, x0 + r - r * KAPPA, y0, x0 + r, y0)
    b.closePath()
    return b.build()


def bowl(
    ctx: DesignContext,
    cx: float,
    cy: float,
    *,
    rx: float | None = None,
    ry: float | None = None,
    thickness: float | None = None,
) -> tuple[Outline, Outline]:
    """Elliptical bowl: returns ``(outer, counter)`` ring.

    Outer radius defaults to half x-height plus overshoot on the vertical axis.
    Counter inset uses ``thickness`` (default ``ctx.stem``).
    """
    outer_ry = (ctx.x_height / 2.0 + ctx.overshoot) if ry is None else ry
    outer_rx = outer_ry if rx is None else rx
    t = ctx.stem if thickness is None else thickness
    inner_rx = max(outer_rx - t, 1.0)
    inner_ry = max(outer_ry - t, 1.0)
    return (_ellipse(cx, cy, outer_rx, outer_ry), _ellipse(cx, cy, inner_rx, inner_ry))


def counter(
    ctx: DesignContext,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
) -> Outline:
    """Standalone elliptical hole (clockwise or CCW — winding fixed at union)."""
    del ctx  # reserved for future contrast-aware counters
    return _ellipse(cx, cy, rx, ry)


def arch(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_bottom: float,
    y_top: float,
    *,
    thickness: float | None = None,
) -> Outline:
    """n/h-style shoulder: outer and inner arches forming a closed trough top.

    The arch sits between two imaginary stems at ``x_left`` and ``x_right``
    (inner faces). ``y_top`` is the outer crown; ``y_bottom`` is where the arch
    meets the stem tops internally.
    """
    t = ctx.stem if thickness is None else thickness
    mid = (x_left + x_right) / 2.0
    # Outer path: left top -> crown -> right top -> down inner -> inner crown -> back
    b = PathBuilder()
    b.moveTo(x_left, y_bottom)
    b.lineTo(x_left, y_top - (x_right - x_left) * 0.15)
    # Outer crown (smooth)
    b.smoothCurveTo(
        mid,
        y_top,
        tangent_out_x=1.0,
        tangent_out_y=0.0,
        handle_ratio=0.42,
        tangent_in_x=0.0,
        tangent_in_y=1.0,
    )
    b.smoothCurveTo(
        x_right,
        y_top - (x_right - x_left) * 0.15,
        tangent_out_x=0.0,
        tangent_out_y=-1.0,
        handle_ratio=0.42,
        tangent_in_x=1.0,
        tangent_in_y=0.0,
    )
    b.lineTo(x_right, y_bottom)
    b.lineTo(x_right - t, y_bottom)
    inner_top = y_top - t
    b.lineTo(x_right - t, inner_top - (x_right - x_left) * 0.12)
    b.smoothCurveTo(
        mid,
        inner_top,
        tangent_out_x=-1.0,
        tangent_out_y=0.0,
        handle_ratio=0.42,
        tangent_in_x=0.0,
        tangent_in_y=1.0,
    )
    b.smoothCurveTo(
        x_left + t,
        inner_top - (x_right - x_left) * 0.12,
        tangent_out_x=0.0,
        tangent_out_y=-1.0,
        handle_ratio=0.42,
        tangent_in_x=-1.0,
        tangent_in_y=0.0,
    )
    b.lineTo(x_left + t, y_bottom)
    b.closePath()
    return b.build()


def u_bowl(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_top: float,
    y_bottom: float,
    *,
    thickness: float | None = None,
) -> Outline:
    """U-shaped trough (two stems + rounded bottom) as one closed outline."""
    t = ctx.stem if thickness is None else thickness
    mid = (x_left + x_right) / 2.0
    depth = (x_right - x_left) * 0.48
    b = PathBuilder()
    # Outer: down left, bottom arc, up right
    b.moveTo(x_left, y_top)
    b.lineTo(x_left, y_bottom + depth)
    b.smoothCurveTo(
        mid,
        y_bottom,
        tangent_out_x=1.0,
        tangent_out_y=0.0,
        handle_ratio=0.45,
        tangent_in_x=0.0,
        tangent_in_y=-1.0,
    )
    b.smoothCurveTo(
        x_right,
        y_bottom + depth,
        tangent_out_x=0.0,
        tangent_out_y=1.0,
        handle_ratio=0.45,
        tangent_in_x=1.0,
        tangent_in_y=0.0,
    )
    b.lineTo(x_right, y_top)
    b.lineTo(x_right - t, y_top)
    b.lineTo(x_right - t, y_bottom + depth)
    inner_bottom = y_bottom + t
    b.smoothCurveTo(
        mid,
        inner_bottom,
        tangent_out_x=-1.0,
        tangent_out_y=0.0,
        handle_ratio=0.45,
        tangent_in_x=0.0,
        tangent_in_y=-1.0,
    )
    b.smoothCurveTo(
        x_left + t,
        y_bottom + depth,
        tangent_out_x=0.0,
        tangent_out_y=1.0,
        handle_ratio=0.45,
        tangent_in_x=-1.0,
        tangent_in_y=0.0,
    )
    b.lineTo(x_left + t, y_top)
    b.closePath()
    return b.build()


def diagonal_stem(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    width: float | None = None,
) -> Outline:
    """Thickened line segment (parallelogram) for diagonals in ``z`` / ``y``."""
    w = ctx.stem if width is None else width
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    half = w / 2.0
    b = PathBuilder()
    b.moveTo(x0 + nx * half, y0 + ny * half)
    b.lineTo(x1 + nx * half, y1 + ny * half)
    b.lineTo(x1 - nx * half, y1 - ny * half)
    b.lineTo(x0 - nx * half, y0 - ny * half)
    b.closePath()
    return b.build()


def hook_terminal(
    ctx: DesignContext,
    x_center: float,
    y_top: float,
    y_bottom: float,
    *,
    hook_radius: float | None = None,
    width: float | None = None,
) -> Outline:
    """Descending stem with a leftward curved hook (lowercase ``j``).

    Outer arc centre sits so the stem's right edge is the arc's east point;
    the hook sweeps through south to the west (open to the left).
    """
    t = ctx.stem if width is None else width
    hr = (abs(y_bottom) * 0.50) if hook_radius is None else hook_radius
    hr = max(hr, t * 1.2)
    left = x_center - t / 2.0
    right = x_center + t / 2.0
    # East point of outer arc == (right, y_bottom + hr)
    outer_cx = right - hr
    outer_cy = y_bottom + hr
    ir = hr - t
    inner_cx = outer_cx
    inner_cy = outer_cy

    b = PathBuilder()
    b.moveTo(left, y_top)
    b.lineTo(right, y_top)
    b.lineTo(right, y_bottom + hr)
    # Outer: 0° (east) → -180° (west), CCW negative = clockwise sweep southward
    b.arcTo(outer_cx, outer_cy, hr, hr, -180, start_angle_deg=0)
    # Now at west outer: (outer_cx - hr, outer_cy)
    # Cap the hook terminal with the stem thickness
    b.lineTo(outer_cx - ir, outer_cy)
    # Inner arc back: 180° → 0° (west to east on inner circle)
    b.arcTo(inner_cx, inner_cy, ir, ir, 0, start_angle_deg=180)
    # Now at (outer_cx + ir, outer_cy) which should be near (left, y_bottom+hr)
    b.lineTo(left, y_bottom + hr)
    b.closePath()
    return b.build()



def tittle(
    ctx: DesignContext,
    cx: float,
    y_bottom: float,
    *,
    size: float | None = None,
) -> Outline:
    """Dot above ``i`` / ``j`` (slightly rounded square by default)."""
    s = ctx.stem * 0.95 if size is None else size
    r = min(ctx.join_radius * 0.6, s * 0.35)
    return rounded_rect(ctx, cx - s / 2.0, y_bottom, cx + s / 2.0, y_bottom + s, radius=r)


def _rect(x0: float, y0: float, x1: float, y1: float) -> Outline:
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    return b.build()


def _ellipse(cx: float, cy: float, rx: float, ry: float) -> Outline:
    b = PathBuilder()
    b.addEllipse(cx, cy, rx, ry)
    return b.build()


def stroke_polyline(
    ctx: DesignContext,
    points: list[tuple[float, float]],
    *,
    width: float | None = None,
    join_radius: float | None = None,
) -> Outline:
    """Centered stroke of a polyline; optional rounded joins from ``ctx.roundness``."""
    import math

    thickness = ctx.stem if width is None else width
    radius = ctx.join_radius if join_radius is None else join_radius
    half = thickness / 2.0
    n = len(points)
    if n < 2:
        raise ValueError("stroke_polyline needs at least two points")

    def seg_n(i: int) -> tuple[float, float]:
        dx = points[i + 1][0] - points[i][0]
        dy = points[i + 1][1] - points[i][1]
        ln = math.hypot(dx, dy) or 1.0
        return (-dy / ln, dx / ln)

    normals = [seg_n(i) for i in range(n - 1)]
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for i in range(n):
        if i == 0:
            nx, ny = normals[0]
        elif i == n - 1:
            nx, ny = normals[-1]
        else:
            ax, ay = normals[i - 1]
            bx, by = normals[i]
            sx, sy = ax + bx, ay + by
            sl = math.hypot(sx, sy)
            if sl < 1e-6:
                nx, ny = ax, ay
            else:
                nx, ny = sx / sl, sy / sl
                dot = max(-1.0, min(1.0, ax * nx + ay * ny))
                m = min(1.0 / max(dot, 0.45), 2.2)
                nx, ny = nx * m, ny * m
        left.append((points[i][0] + nx * half, points[i][1] + ny * half))
        right.append((points[i][0] - nx * half, points[i][1] - ny * half))

    b = PathBuilder()
    if radius <= 0 or n < 3:
        b.moveTo(*left[0])
        for pt in left[1:]:
            b.lineTo(*pt)
        b.lineTo(*right[-1])
        for pt in reversed(right[:-1]):
            b.lineTo(*pt)
        b.closePath()
        return b.build()

    b.moveTo(*left[0])
    for i in range(1, len(left) - 1):
        b.roundedCornerTo(
            left[i][0], left[i][1], left[i + 1][0], left[i + 1][1], radius, continue_to_end=False
        )
    b.lineTo(*left[-1])
    b.lineTo(*right[-1])
    for i in range(len(right) - 2, 0, -1):
        nxt = right[i - 1]
        b.roundedCornerTo(
            right[i][0], right[i][1], nxt[0], nxt[1], radius, continue_to_end=False
        )
    b.lineTo(*right[0])
    b.closePath()
    return b.build()



# ---------------------------------------------------------------------------
# Extra primitives for agent composition (Three.js-style catalog depth)
# ---------------------------------------------------------------------------


def capsule(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    radius: float | None = None,
) -> Outline:
    """Stadium / capsule: rectangle with semicircle caps on the short axis.

    Useful for soft terminals and even-colour bars without sharp corners.
    """
    r = (min(abs(x1 - x0), abs(y1 - y0)) / 2.0) if radius is None else radius
    # Orient: if wider than tall, caps on left/right; else top/bottom.
    w, h = abs(x1 - x0), abs(y1 - y0)
    b = PathBuilder()
    if w >= h:
        r = min(r, h / 2.0)
        cy = (y0 + y1) / 2.0
        left_cx, right_cx = x0 + r, x1 - r
        b.moveTo(left_cx, y0)
        b.lineTo(right_cx, y0)
        b.arcTo(right_cx, cy, r, r, 270, start_angle_deg=-90)
        b.lineTo(left_cx, y1)
        b.arcTo(left_cx, cy, r, r, 90, start_angle_deg=90)
        b.closePath()
    else:
        r = min(r, w / 2.0)
        cx = (x0 + x1) / 2.0
        bot_cy, top_cy = y0 + r, y1 - r
        b.moveTo(x0, bot_cy)
        b.arcTo(cx, bot_cy, r, r, 0, start_angle_deg=180)
        b.lineTo(x1, top_cy)
        b.arcTo(cx, top_cy, r, r, 180, start_angle_deg=0)
        b.closePath()
    return b.build()


def crossbar(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_center: float,
    *,
    thickness: float | None = None,
) -> Outline:
    """Centered horizontal crossbar (``e``, ``A``, ``H``)."""
    t = ctx.thin if thickness is None else thickness
    return horizontal_bar(ctx, x_left, x_right, y_center - t / 2.0, thickness=t)


def wedge(
    ctx: DesignContext,
    tip_x: float,
    tip_y: float,
    base_x0: float,
    base_y0: float,
    base_x1: float,
    base_y1: float,
) -> Outline:
    """Triangle wedge — building block for ink traps and tapered joins."""
    del ctx
    b = PathBuilder()
    b.moveTo(tip_x, tip_y)
    b.lineTo(base_x0, base_y0)
    b.lineTo(base_x1, base_y1)
    b.closePath()
    return b.build()


def fillet_pad(
    ctx: DesignContext,
    x: float,
    y: float,
    *,
    radius: float | None = None,
    quadrant: int = 0,
) -> Outline:
    """Quarter-disk pad to soften a stem/bowl join before boolean union.

    ``quadrant`` 0..3 matches quarter-circle cubics (0=NE, 1=NW, 2=SW, 3=SE).
    Place the pad so its centre sits at the concave notch corner, then call
    :meth:`~typekernel.parts.compose.GlyphAssembler.union_solids`.
    """
    from typekernel.geo.path_helpers import Quadrant, quarter_circle_cubics

    r = ctx.join_radius if radius is None else radius
    if r <= 0:
        return _rect(x, y, x + 1e-3, y + 1e-3)
    q = quadrant % 4
    p0, p1, p2, p3 = quarter_circle_cubics(x, y, r, r, q)  # type: ignore[arg-type]
    del Quadrant  # imported for agents reading the signature docs
    b = PathBuilder()
    b.moveTo(x, y)
    b.lineTo(p0.x, p0.y)
    b.curveTo(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
    b.closePath()
    return b.build()


def terminal_ball(
    ctx: DesignContext,
    cx: float,
    cy: float,
    *,
    radius: float | None = None,
) -> Outline:
    """Circular ball terminal (stroke end blob)."""
    r = ctx.stem * 0.55 if radius is None else radius
    return _ellipse(cx, cy, r, r)


def terminal_sheared(
    ctx: DesignContext,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    *,
    shear: float = 0.35,
) -> Outline:
    """Parallelogram terminal / cut end (sheared rectangle)."""
    t = abs(y1 - y0) if abs(y1 - y0) > 1e-9 else ctx.stem
    s = shear * t
    b = PathBuilder()
    b.moveTo(x0 + s, y0)
    b.lineTo(x1 + s, y0)
    b.lineTo(x1 - s, y1)
    b.lineTo(x0 - s, y1)
    b.closePath()
    return b.build()


def serif_bracket(
    ctx: DesignContext,
    x_stem: float,
    y: float,
    *,
    side: str = "left",
    length: float | None = None,
    thickness: float | None = None,
) -> Outline:
    """Simple bracket serif stub (rectangular + slight bracket curve).

    Enough for agents to attach serifs while iterating; not a full serif
    family. ``side`` is ``\"left\"`` or ``\"right\"`` relative to the stem face.
    """
    length = ctx.stem * 1.1 if length is None else length
    thickness = ctx.thin * 0.55 if thickness is None else thickness
    if side == "left":
        x0, x1 = x_stem - length, x_stem
    elif side == "right":
        x0, x1 = x_stem, x_stem + length
    else:
        raise ValueError("side must be 'left' or 'right'")
    # Mild bracket: outer corner rounded toward the stem.
    r = min(ctx.join_radius * 0.5, thickness * 0.8, length * 0.4)
    return rounded_rect(ctx, x0, y, x1, y + thickness, radius=r)


def ink_trap(
    ctx: DesignContext,
    *_args: object,
    **_kwargs: object,
) -> Outline:
    """Reserved ink-trap primitive — not implemented yet.

    Agents should leave a wedge-shaped notch at acute joins and call this
    once a trap policy lands. Until then, compose with :func:`wedge` and
    boolean difference.
    """
    del ctx, _args, _kwargs
    raise NotImplementedError(
        "ink_trap is reserved; use wedge() + boolean difference for now"
    )


def shoulder(
    ctx: DesignContext,
    x_left: float,
    x_right: float,
    y_bottom: float,
    y_top: float,
    *,
    thickness: float | None = None,
) -> Outline:
    """Alias for :func:`arch` — n/h/m shoulder trough."""
    return arch(ctx, x_left, x_right, y_bottom, y_top, thickness=thickness)


def smooth_hook(
    ctx: DesignContext,
    x_right: float,
    y_top: float,
    y_bottom: float,
    *,
    radius: float | None = None,
    tail: float | None = None,
    width: float | None = None,
) -> Outline:
    """Descending stem that turns left in one continuous quarter arc (``j``).

    Stem → arc → horizontal tail with tangent-continuous joins (no polyline
    facets). ``x_right`` is the stem's right edge, ``y_bottom`` the outer
    bottom of the hook, ``tail`` how far the terminal reaches left of the
    arc. Ends are flat terminals.
    """
    t = ctx.stem if width is None else width
    r = max(t * 1.15, (y_top - y_bottom) * 0.30) if radius is None else radius
    tail_len = r * 0.55 if tail is None else tail
    left = x_right - t
    cx, cy = x_right - r, y_bottom + r
    b = PathBuilder()
    b.moveTo(left, y_top)
    b.lineTo(x_right, y_top)
    b.lineTo(x_right, cy)
    b.arcTo(cx, cy, r, r, -90.0, start_angle_deg=0.0)
    b.lineTo(cx - tail_len, y_bottom)
    b.lineTo(cx - tail_len, y_bottom + t)
    b.lineTo(cx, y_bottom + t)
    b.arcTo(cx, cy, r - t, r - t, 0.0, start_angle_deg=-90.0)
    b.lineTo(left, y_top)
    b.closePath()
    return b.build()
