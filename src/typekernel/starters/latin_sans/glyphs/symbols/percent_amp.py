"""percent and ampersand ."""
from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


def _lsb(system):
    return float(system.tokens.get("lsb_lc", 40.0)) * 0.45

@glyph("percent", unicodes=(0x0025,), group="symbol", traits=("symbol",))
def percent(system: System):
    st = float(system.stem["lc"]) * 0.7; thin = st * 0.9; xh = float(system.zones.x); lsb = _lsb(system)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("percent", 640))
    top = bowl((lsb + w * 0.28, xh * 0.72), w * 0.16, xh * 0.16, thick=st, thin=thin, exponent=exp, name="bowl.t")
    bot = bowl((lsb + w * 0.72, xh * 0.28), w * 0.16, xh * 0.16, thick=st, thin=thin, exponent=exp, name="bowl.b")
    l, r = diagonal_band((lsb + w * 0.78, xh * 0.9), (lsb + w * 0.22, xh * 0.1), weight=st, compensate=True)
    slash = (Writer().start(l.start).corner("diag.l.a").fragment(l).corner("diag.l.b")
             .line(r.start).corner("diag.r.a").fragment(r).corner("diag.r.b").line(l.start).close().build())
    return top + bot + slash

@glyph("ampersand", unicodes=(0x0026,), group="symbol", traits=("symbol",))
def ampersand(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); lsb = _lsb(system)
    from typekernel.anatomy import open_bowl
    ov = float(system.overshoot.round); exp = float(system.tokens.get("bowl_exponent", 2.15))
    w = float(WIDTHS.get("ampersand", 620))
    # Structural approx: upper loop + lower bowl + diagonal arm
    upper = open_bowl((lsb + w * 0.42, xh * 0.72), w * 0.32, xh * 0.28, thick=st, thin=thin, aperture=0.35, open_side="right", exponent=exp, overshoot=ov * 0.2, name="bowl.t")
    lower = open_bowl((lsb + w * 0.45, xh * 0.32), w * 0.4, xh * 0.35, thick=st, thin=thin, aperture=0.3, open_side="left", exponent=exp, overshoot=ov * 0.3, name="bowl.b")
    l, r = diagonal_band((lsb + w * 0.35, xh * 0.55), (lsb + w * 0.92, xh * 0.08), weight=st * 0.9, compensate=True)
    arm = (Writer().start(l.start).corner("diag.l.a").fragment(l).corner("diag.l.b")
           .line(r.start).corner("diag.r.a").fragment(r).corner("diag.r.b").line(l.start).close().build())
    return upper + lower + arm
