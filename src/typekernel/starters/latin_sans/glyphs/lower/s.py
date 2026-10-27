"""Round glyph s — upper and lower open bowls overlapping at the waist."""

from __future__ import annotations

from elements import arch_span

from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


def _open_bowl(
    *,
    cx: float,
    cy: float,
    rx: float,
    ry: float,
    thickness: float,
    tension: float,
    open_right: bool,
    tag: str,
):
    """Nearly elliptical ring with a right or left aperture."""
    irx = max(rx - thickness, 1.0)
    iry = max(ry - thickness * 0.85, 1.0)
    # Approximate ellipse with four arch spans (N,W,S,E halves as two arches each).
    # Simpler: build left-open or right-open using top/bottom/side arches.
    if open_right:
        # Path travels left side: top → west → bottom, then return on inner.
        top = arch_span(cx + rx * 0.35, cy + ry, cx - rx, cy, cy + ry + 4, tension=tension)
        bot = arch_span(cx - rx, cy, cx + rx * 0.35, cy - ry, cy - ry - 4, tension=tension)
        top_i = arch_span(
            cx - irx, cy, cx + irx * 0.2, cy + iry, cy + iry - thickness * 0.2, tension=tension
        )
        bot_i = arch_span(
            cx + irx * 0.2, cy - iry, cx - irx, cy, cy - iry + thickness * 0.2, tension=tension
        )
        w = Writer()
        w.start(top.start).corner(f"{tag}.top.o")
        w.fragment(top).corner(f"{tag}.west.o")
        w.fragment(bot).corner(f"{tag}.bot.o")
        w.line(bot_i.start).corner(f"{tag}.bot.i")
        w.fragment(bot_i)
        if abs(bot_i.end.x - top_i.start.x) > 1e-6 or abs(bot_i.end.y - top_i.start.y) > 1e-6:
            w.line(top_i.start)
        w.corner(f"{tag}.west.i")
        w.fragment(top_i).corner(f"{tag}.top.i")
        w.line(top.start)
        return w.close().build()
    # open left (mirror): start bottom-rightish, go east side upward
    top = arch_span(cx - rx * 0.35, cy + ry, cx + rx, cy, cy + ry + 4, tension=tension)
    bot = arch_span(cx + rx, cy, cx - rx * 0.35, cy - ry, cy - ry - 4, tension=tension)
    top_i = arch_span(
        cx + irx, cy, cx - irx * 0.2, cy + iry, cy + iry - thickness * 0.2, tension=tension
    )
    bot_i = arch_span(
        cx - irx * 0.2, cy - iry, cx + irx, cy, cy - iry + thickness * 0.2, tension=tension
    )
    w = Writer()
    w.start(top.start).corner(f"{tag}.top.o")
    w.fragment(top).corner(f"{tag}.east.o")
    w.fragment(bot).corner(f"{tag}.bot.o")
    w.line(bot_i.start).corner(f"{tag}.bot.i")
    w.fragment(bot_i)
    if abs(bot_i.end.x - top_i.start.x) > 1e-6 or abs(bot_i.end.y - top_i.start.y) > 1e-6:
        w.line(top_i.start)
    w.corner(f"{tag}.east.i")
    w.fragment(top_i).corner(f"{tag}.top.i")
    w.line(top.start)
    return w.close().build()


@glyph("s", group="lc.round")
def s(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    width = float(system.tokens["s_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round)
    cx = lsb + width / 2.0
    rx = width / 2.0 * 0.92
    # Upper bowl open on the right, centered in top half.
    upper = _open_bowl(
        cx=cx,
        cy=xh * 0.72,
        rx=rx,
        ry=xh * 0.30 + ov * 0.3,
        thickness=st,
        tension=tension,
        open_right=True,
        tag="s.upper",
    )
    # Lower bowl open on the left, centered in bottom half.
    lower = _open_bowl(
        cx=cx,
        cy=xh * 0.28,
        rx=rx,
        ry=xh * 0.30 + ov * 0.3,
        thickness=st,
        tension=tension,
        open_right=False,
        tag="s.lower",
    )
    return upper + lower
