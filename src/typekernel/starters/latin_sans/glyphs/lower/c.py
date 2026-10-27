"""Round glyph c — open bowl (outer arc with aperture on the right)."""

from __future__ import annotations

from typekernel.draw import Writer, superellipse_quarter
from typekernel.project import glyph
from typekernel.system import System


@glyph("c", group="lc.round")
def c(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(system.tokens["c_width"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    cx = lsb + width / 2.0
    cy = xh / 2.0
    rx, ry = width / 2.0, xh / 2.0 + ov
    irx, iry = max(rx - st, 1.0), max(ry - thin, 1.0)
    # Open on the right: use quarters 1,2,3 (top, left, bottom) for outer/inner.
    # Quadrants: 0=E→N, 1=N→W, 2=W→S, 3=S→E. Skip most of 0 and 3 aperture.
    # Build as nearly-full ring with a vertical aperture cut on the right.
    # Simpler: three outer quarters + three inner, connected at aperture lips.
    o1 = superellipse_quarter((cx, cy), rx, ry, 1, exponent=exp)
    o2 = superellipse_quarter((cx, cy), rx, ry, 2, exponent=exp)
    o3 = superellipse_quarter((cx, cy), rx, ry, 3, exponent=exp)
    # Trim aperture: start a bit past south-east, end before north-east.
    # Use partial: start at end of q0 (north) via q1,q2 into start of q3...
    # Practical approach — full ring minus a rectangular bite on the right via
    # single contour from aperture top lip around to bottom lip.
    i1 = superellipse_quarter((cx, cy), irx, iry, 1, exponent=exp)
    i2 = superellipse_quarter((cx, cy), irx, iry, 2, exponent=exp)
    i3 = superellipse_quarter((cx, cy), irx, iry, 3, exponent=exp)
    # Aperture lips near east: outer at ~ (cx+rx*0.75, cy±gap)
    # Path: aperture top (outer) → around NW S → aperture bottom (outer)
    # → inward to inner bottom → around reverse → aperture top inner → close.
    # Start at north-east-ish on outer (start of q1 = north point).
    w = Writer()
    w.start(o1.start).corner("c.aperture.top.o")
    w.fragment(o1).fragment(o2).fragment(o3)
    w.corner("c.aperture.bot.o")
    # Across aperture to inner (same y roughly at o3.end which is east)
    # o3 ends at east point (cx+rx, cy). Move left to inner east, then reverse
    # through i3,i2,i1.
        # Connect outer east to a point just inside aperture at same height then
    # to inner east going the other way — use line to inner end of i3 (east).
    # i3: south→east, ends at (cx+irx, cy).
    w.line(i3.end).corner("c.aperture.bot.i")
    # reverse inner: east → south → west → north
    w.fragment(i3.reversed()).fragment(i2.reversed()).fragment(i1.reversed())
    w.corner("c.aperture.top.i")
    w.line(o1.start)
    return w.close().build()
