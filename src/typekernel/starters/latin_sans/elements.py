"""Project elements for latin-sans — arch, bowl (no letter-named builders)."""

from __future__ import annotations

from dataclasses import dataclass

from typekernel.draw import (
    Drawing,
    Fragment,
    Writer,
    diagonal_band,
    superellipse_quarter,
    tensioned_arc,
)
from typekernel.system import System

__all__ = ["Arch", "arch", "arch_span", "bowl", "cap_stem", "crossbar", "diagonal_stroke", "shoulder_trough", "stem_rect"]


@dataclass(frozen=True, slots=True)
class Arch:
    """Open shoulder fragments for n/h-style joins."""

    outer: Fragment
    inner: Fragment


def arch_span(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    crown_y: float,
    *,
    tension: float,
) -> Fragment:
    """Two G1 cubics from ``(x0,y0)`` to ``(x1,y1)`` via a horizontal crown."""
    mid_x = (x0 + x1) / 2.0
    sx = 1.0 if x1 >= x0 else -1.0
    left = tensioned_arc(
        (x0, y0), (sx, 0.0), (mid_x, crown_y), (sx, 0.0), tension=tension
    )
    right = tensioned_arc(
        (mid_x, crown_y), (sx, 0.0), (x1, y1), (sx, 0.0), tension=tension
    )
    return Fragment(left.segments + right.segments)


def arch(system: System, *, left: float, counter: float) -> Arch:
    """n/h-style shoulder: outer and inner open fragments.

    ``left`` is the x of the left stem's inner face (and usually the stem
    thickness when the outer face sits at 0). ``counter`` is the inner gap.
    Outer runs left→right at x-height; inner runs right→left at the same
    join y with a lower crown (ARCHITECTURE.md §3 example).
    """
    xh = float(system.zones.x)
    stem = float(left)
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    right_outer = left + counter + stem
    right_inner = left + counter
    outer_crown = xh + float(system.overshoot.round) * 0.35
    inner_crown = xh - stem + float(system.overshoot.round) * 0.15
    return Arch(
        outer=arch_span(left, xh, right_outer, xh, outer_crown, tension=tension),
        inner=arch_span(
            right_inner, xh, left, xh, inner_crown, tension=tension
        ),
    )


def bowl(
    system: System,
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float | None = None,
) -> Drawing:
    """Elliptical/superellipse ring: ink outer + counter hole.

    Vertical ``ry`` should already include round overshoot when desired.
    """
    stem = float(system.stem["lc"] if thickness is None else thickness)
    thin = float(system.stem.get("lc_h", stem * 0.85))
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    outer_rx, outer_ry = float(rx), float(ry)
    inner_rx = max(outer_rx - stem, 1.0)
    inner_ry = max(outer_ry - thin, 1.0)

    def _ring(rx_: float, ry_: float, *, counter: bool = False) -> Drawing:
        frags = [
            superellipse_quarter((cx, cy), rx_, ry_, q, exponent=exp)
            for q in range(4)
        ]
        w = Writer().start(frags[0].start)
        for frag in frags:
            w.fragment(frag)
        return w.close(role="counter" if counter else "ink").build()

    return _ring(outer_rx, outer_ry) + _ring(inner_rx, inner_ry, counter=True)


def cap_stem(
    system: System,
    *,
    x: float,
    y0: float,
    y1: float,
    tag_prefix: str,
) -> Drawing:
    """Vertical uppercase stem rectangle with corner tags for future serifs."""
    w = float(system.stem["uc"])
    return (
        Writer()
        .start((x, y0))
        .corner(f"{tag_prefix}.foot.o")
        .line((x, y1))
        .corner(f"{tag_prefix}.top.o")
        .line((x + w, y1))
        .corner(f"{tag_prefix}.top.i")
        .line((x + w, y0))
        .corner(f"{tag_prefix}.foot.i")
        .line((x, y0))
        .close()
        .build()
    )


def crossbar(
    system: System,
    *,
    x0: float,
    x1: float,
    cy: float,
    tag_prefix: str = "bar",
) -> Drawing:
    """Horizontal bar spanning ``x0``..``x1`` centered on ``cy``."""
    t = float(system.tokens.get("bar_thickness", system.stem["uc"] * 0.85))
    y0, y1 = cy - t / 2.0, cy + t / 2.0
    return (
        Writer()
        .start((x0, y0))
        .corner(f"{tag_prefix}.bl")
        .line((x0, y1))
        .corner(f"{tag_prefix}.tl")
        .line((x1, y1))
        .corner(f"{tag_prefix}.tr")
        .line((x1, y0))
        .corner(f"{tag_prefix}.br")
        .line((x0, y0))
        .close()
        .build()
    )


def stem_rect(
    x0: float,
    x1: float,
    y0: float,
    y1: float,
    *,
    prefix: str,
) -> Drawing:
    """Closed vertical stem with corner tags for future serifs."""
    return (
        Writer()
        .start((x0, y0))
        .corner(f"{prefix}.foot.o")
        .line((x0, y1))
        .corner(f"{prefix}.top.o")
        .line((x1, y1))
        .corner(f"{prefix}.top.i")
        .line((x1, y0))
        .corner(f"{prefix}.foot.i")
        .line((x0, y0))
        .close()
        .build()
    )


def shoulder_trough(
    system: System,
    *,
    x_left: float,
    x_right: float,
    y_top: float,
    y_bot: float,
    tag_prefix: str = "arch",
) -> Drawing:
    """Closed overlapping shoulder between ``x_left``..``x_right``.

    Top edge is a raised arch at ``y_top``; bottom is a lower counter arch at
    ``y_bot``. Intended to overlap vertical stems (ARCHITECTURE.md overlap).
    """
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round) * 0.35
    outer = arch_span(
        x_left, y_top, x_right, y_top, y_top + ov + 8.0, tension=tension
    )
    inner = arch_span(
        x_right, y_bot, x_left, y_bot, y_bot - abs(y_top - y_bot) * 0.2, tension=tension
    )
    return (
        Writer()
        .start((x_left, y_bot))
        .corner(f"{tag_prefix}.l.bot")
        .line((x_left, y_top))
        .corner(f"{tag_prefix}.l.top")
        .fragment(outer)
        .corner(f"{tag_prefix}.r.top")
        .line((x_right, y_bot))
        .corner(f"{tag_prefix}.r.bot")
        .fragment(inner)
        .close()
        .build()
    )



def diagonal_stroke(
    p_top: tuple[float, float],
    p_bottom: tuple[float, float],
    *,
    weight: float,
    tag_prefix: str = "diag",
    compensate: bool = True,
) -> Drawing:
    """Closed parallelogram for one diagonal stem via ``diagonal_band``.

    ``p_top`` / ``p_bottom`` are the stroke centerline endpoints (top → bottom).
    """
    left, right = diagonal_band(
        p_top, p_bottom, weight=weight, compensate=compensate
    )
    # left: top→bot; right: bot→top. Join across tip then head.
    return (
        Writer()
        .start(left.start)
        .corner(f"{tag_prefix}.top.l")
        .fragment(left)
        .corner(f"{tag_prefix}.bot.l")
        .line(right.start)
        .corner(f"{tag_prefix}.bot.r")
        .fragment(right)
        .corner(f"{tag_prefix}.top.r")
        .line(left.start)
        .close()
        .build()
    )
