"""O-group glyph C — open capital bowl."""

from __future__ import annotations

from typekernel.draw import Writer, superellipse_quarter
from typekernel.project import glyph
from typekernel.system import System


@glyph("C", group="uc.bowl")
def glyph_C(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    width = float(system.tokens["C_width"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    cx = lsb + width / 2.0
    cy = cap / 2.0
    rx, ry = width / 2.0, cap / 2.0 + ov
    irx, iry = max(rx - st, 1.0), max(ry - thin, 1.0)
    o1 = superellipse_quarter((cx, cy), rx, ry, 1, exponent=exp)
    o2 = superellipse_quarter((cx, cy), rx, ry, 2, exponent=exp)
    o3 = superellipse_quarter((cx, cy), rx, ry, 3, exponent=exp)
    i1 = superellipse_quarter((cx, cy), irx, iry, 1, exponent=exp)
    i2 = superellipse_quarter((cx, cy), irx, iry, 2, exponent=exp)
    i3 = superellipse_quarter((cx, cy), irx, iry, 3, exponent=exp)
    w = Writer()
    w.start(o1.start).corner("C.aperture.top.o")
    w.fragment(o1).fragment(o2).fragment(o3)
    w.corner("C.aperture.bot.o")
    w.line(i3.end).corner("C.aperture.bot.i")
    w.fragment(i3.reversed()).fragment(i2.reversed()).fragment(i1.reversed())
    w.corner("C.aperture.top.i")
    w.line(o1.start)
    return w.close().build()
