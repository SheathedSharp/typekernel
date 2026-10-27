"""Control glyph n — stems + overlapping arch trough (ARCHITECTURE.md §3)."""

from __future__ import annotations

from typekernel.draw import Fragment, Writer, tensioned_arc
from typekernel.project import glyph
from typekernel.system import System


def _arch_span(
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    crown_y: float,
    *,
    tension: float,
) -> Fragment:
    mid = (x0 + x1) / 2.0
    sx = 1.0 if x1 >= x0 else -1.0
    a = tensioned_arc(
        (x0, y0), (sx, 0.0), (mid, crown_y), (sx, 0.0), tension=tension
    )
    b = tensioned_arc(
        (mid, crown_y), (sx, 0.0), (x1, y1), (sx, 0.0), tension=tension
    )
    return Fragment(a.segments + b.segments)


def _stem_rect(x0: float, x1: float, y0: float, y1: float, prefix: str):
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


@glyph("n", group="lc.straight")
def n(system: System):
    """Straight stems with an overlapping shoulder trough.

    Overlap construction (ARCHITECTURE.md §3.2): stems and shoulder are
    separate closed contours that overlap at the joins — no zero-thickness meet.
    """
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["n_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round) * 0.35

    left = _stem_rect(lsb, lsb + st, 0.0, xh, "stem.l")
    right = _stem_rect(lsb + width - st, lsb + width, 0.0, xh, "stem.r")

    # Trough spans into both stems so overlap has positive area.
    inset = st * 0.35
    x_l = lsb + inset
    x_r = lsb + width - inset
    y_top = xh
    y_bot = xh - st + ov
    outer = _arch_span(x_l, y_top, x_r, y_top, y_top + ov + 8.0, tension=tension)
    inner = _arch_span(x_r, y_bot, x_l, y_bot, y_bot - (st * 0.15), tension=tension)

    trough = (
        Writer()
        .start((x_l, y_bot))
        .corner("arch.l.bot")
        .line((x_l, y_top))
        .corner("arch.l.top")
        .fragment(outer)
        .corner("arch.r.top")
        .line((x_r, y_bot))
        .corner("arch.r.bot")
        .fragment(inner)
        .close()
        .build()
    )
    return left + right + trough
