"""Explicit join-cleanup operators.

Join cleanup is a named optical policy, never a silent ``simplify(tol)`` that
destroys extrema and handle intent.
"""

from __future__ import annotations

import math
from typing import Literal

from typekernel.geo.boolean import boolean_op
from typekernel.geo.contour import signed_area
from typekernel.geo.joins import join_angles
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.geo.smoothness import incoming_tangent, outgoing_tangent

JoinPolicy = Literal["noop", "tangent_fix", "ink_trap"]

Segment = LineSegment | CubicSegment


def cleanup_joins(
    outline: Outline,
    policy: JoinPolicy = "noop",
    *,
    depth: float | None = None,
    opening_deg: float = 28.0,
    min_turn_deg: float = 55.0,
    max_turn_deg: float = 170.0,
) -> Outline:
    """Apply an explicit join-cleanup policy; return a (possibly new) outline.

    Policies:

    - ``noop`` (default): return the same outline object unchanged. No geometry
      is rewritten, so handles and extrema stay intact.
    - ``tangent_fix``: reserved — raise ``NotImplementedError``.
    - ``ink_trap``: punch parameterized wedges at sharp internal corners /
      crotches (``depth``, ``opening_deg``, turn window). Uses boolean
      difference (requires pathops). Does not call ``simplify``.

    Calling ``simplify`` (or any tolerance-based path reduction) under any
    policy name is forbidden here.
    """
    if policy == "noop":
        return outline
    if policy == "tangent_fix":
        raise NotImplementedError(
            "cleanup_joins policy 'tangent_fix' is reserved and not implemented"
        )
    if policy == "ink_trap":
        return _apply_ink_traps(
            outline,
            depth=12.0 if depth is None else depth,
            opening_deg=opening_deg,
            min_turn_deg=min_turn_deg,
            max_turn_deg=max_turn_deg,
        )
    raise ValueError(f"unknown join cleanup policy: {policy!r}")


def _seg_end(seg: Segment) -> Point:
    return seg.p1 if isinstance(seg, LineSegment) else seg.p3


def _wedge_trap(
    apex_x: float,
    apex_y: float,
    *,
    depth: float,
    opening_deg: float,
    bisector_deg: float,
) -> Outline:
    """Local wedge (mirrors parts.ink_trap) so optics does not import parts."""
    half_open = math.radians(opening_deg / 2.0)
    base_half = depth * math.tan(half_open)
    rad = math.radians(bisector_deg)
    bx, by = math.cos(rad), math.sin(rad)
    px, py = -by, bx
    base_cx = apex_x + bx * depth
    base_cy = apex_y + by * depth
    b = PathBuilder()
    b.moveTo(apex_x, apex_y)
    b.lineTo(base_cx - px * base_half, base_cy - py * base_half)
    b.lineTo(base_cx + px * base_half, base_cy + py * base_half)
    b.closePath()
    return b.build()


def _apply_ink_traps(
    outline: Outline,
    *,
    depth: float,
    opening_deg: float,
    min_turn_deg: float,
    max_turn_deg: float,
) -> Outline:
    """Difference ink-trap wedges at concave sharp joins."""
    if depth <= 0:
        raise ValueError(f"depth must be positive, got {depth!r}")
    if opening_deg <= 0 or opening_deg >= 180:
        raise ValueError(f"opening_deg must be in (0, 180), got {opening_deg!r}")

    traps: list[Outline] = []
    for contour in outline.contours:
        segs = contour.segments
        n = len(segs)
        if n < 2 or not contour.closed:
            continue
        ccw = signed_area(contour) > 0.0
        angles = join_angles(contour)
        for i, ang in enumerate(angles):
            if ang < min_turn_deg or ang > max_turn_deg:
                continue
            a = segs[i]
            b = segs[(i + 1) % n]
            apex = _seg_end(a)
            tin = incoming_tangent(a)
            tout = outgoing_tangent(b)
            cross = tin.x * tout.y - tin.y * tout.x
            concave = (cross < 0) if ccw else (cross > 0)
            if not concave:
                continue
            lin = math.hypot(tin.x, tin.y) or 1.0
            lout = math.hypot(tout.x, tout.y) or 1.0
            ux_in, uy_in = tin.x / lin, tin.y / lin
            ux_out, uy_out = tout.x / lout, tout.y / lout
            if ccw:
                n_in = (-uy_in, ux_in)
                n_out = (-uy_out, ux_out)
            else:
                n_in = (uy_in, -ux_in)
                n_out = (uy_out, -ux_out)
            bx = n_in[0] + n_out[0]
            by = n_in[1] + n_out[1]
            bl = math.hypot(bx, by)
            if bl < 1e-9:
                bx, by = -(ux_in + ux_out), -(uy_in + uy_out)
                bl = math.hypot(bx, by) or 1.0
            bx, by = bx / bl, by / bl
            bis_deg = math.degrees(math.atan2(by, bx))
            traps.append(
                _wedge_trap(
                    apex.x,
                    apex.y,
                    depth=depth,
                    opening_deg=opening_deg,
                    bisector_deg=bis_deg,
                )
            )

    if not traps:
        return outline

    result = outline
    for trap in traps:
        result = boolean_op(result, trap, "difference")
    return result
