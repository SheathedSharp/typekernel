"""Currency and related symbols ."""
from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl, crossbar, open_bowl, stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


def _lsb(system):
    return float(system.tokens.get("lsb_lc", 40.0)) * 0.45

@glyph("dollar", unicodes=(0x0024,), group="symbol", traits=("symbol",))
def dollar(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); asc = float(system.zones.asc); lsb = _lsb(system)
    ov = float(system.overshoot.round); exp = float(system.tokens.get("bowl_exponent", 2.15))
    w = float(WIDTHS.get("dollar", 480))
    # S-like via two open bowls stacked + vertical stroke
    top = open_bowl((lsb + w / 2, xh * 0.72), w * 0.42, xh * 0.28, thick=st, thin=thin, aperture=0.45, open_side="left", exponent=exp, overshoot=ov * 0.3, name="bowl.t")
    bot = open_bowl((lsb + w / 2, xh * 0.28), w * 0.42, xh * 0.28, thick=st, thin=thin, aperture=0.45, open_side="right", exponent=exp, overshoot=ov * 0.3, name="bowl.b")
    stroke = stem(lsb + (w - st * 0.7) / 2, lsb + (w + st * 0.7) / 2, xh * 0.02, asc * 0.88, name="stem", foot="none", top="none")
    return top + bot + stroke

@glyph("cent", unicodes=(0x00A2,), group="symbol", traits=("symbol",))
def cent(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); lsb = _lsb(system); ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("cent", 420))
    ring = open_bowl((lsb + w / 2, xh / 2), w / 2 * 0.9, xh / 2, thick=st, thin=thin, aperture=0.35, open_side="right", exponent=exp, overshoot=ov, name="bowl")
    stroke = stem(lsb + (w - st * 0.7) / 2, lsb + (w + st * 0.7) / 2, xh * 0.05, xh * 0.95, name="stem", foot="none", top="none")
    return ring + stroke

@glyph("sterling", unicodes=(0x00A3,), group="symbol", traits=("symbol",))
def sterling(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); asc = float(system.zones.asc); lsb = _lsb(system)
    w = float(WIDTHS.get("sterling", 500))
    body = stem(lsb + w * 0.35, lsb + w * 0.35 + st, 0.0, asc * 0.85, name="stem")
    top = crossbar(lsb + w * 0.35, lsb + w * 0.85, asc * 0.85 - thin / 2, thick=thin, name="bar.t", ends="none")
    bar = crossbar(lsb + w * 0.15, lsb + w * 0.75, xh * 0.55, thick=thin, name="bar", ends="none")
    base = crossbar(lsb + w * 0.2, lsb + w * 0.85, thin / 2, thick=thin, name="bar.b", ends="none")
    return body + top + bar + base

@glyph("yen", unicodes=(0x00A5,), group="symbol", traits=("symbol",))
def yen(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); cap = float(system.zones.cap); lsb = _lsb(system)
    from typekernel.anatomy import diagonal_pair
    w = float(WIDTHS.get("yen", 560))
    v = diagonal_pair((lsb + w / 2, cap * 0.55), (lsb, cap), (lsb + w, cap), weight=st, name="diag")
    stem_v = stem(lsb + (w - st) / 2, lsb + (w + st) / 2, 0.0, cap * 0.55, name="stem")
    b1 = crossbar(lsb + w * 0.2, lsb + w * 0.8, xh * 0.42, thick=thin, name="bar.1", ends="none")
    b2 = crossbar(lsb + w * 0.2, lsb + w * 0.8, xh * 0.28, thick=thin, name="bar.2", ends="none")
    return v + stem_v + b1 + b2

@glyph("currency", unicodes=(0x00A4,), group="symbol", traits=("symbol", "no-stem"))
def currency(system: System):
    st = float(system.stem["lc"]) * 0.7; thin = st * 0.9; xh = float(system.zones.x); lsb = _lsb(system)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("currency", 480))
    ring = bowl((lsb + w / 2, xh / 2), w * 0.28, xh * 0.28, thick=st, thin=thin, exponent=exp, name="bowl")
    parts = [ring]
    for i, (x0, y0, x1, y1) in enumerate([
        (lsb + w * 0.12, xh * 0.88, lsb + w * 0.32, xh * 0.68),
        (lsb + w * 0.88, xh * 0.88, lsb + w * 0.68, xh * 0.68),
        (lsb + w * 0.12, xh * 0.12, lsb + w * 0.32, xh * 0.32),
        (lsb + w * 0.88, xh * 0.12, lsb + w * 0.68, xh * 0.32),
    ]):
        l, r = diagonal_band((x0, y0), (x1, y1), weight=st * 0.85, compensate=False)
        parts.append(Writer().start(l.start).corner(f"arm.{i}.a").fragment(l).corner(f"arm.{i}.b")
                     .line(r.start).corner(f"arm.{i}.c").fragment(r).corner(f"arm.{i}.d").line(l.start).close().build())
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out

@glyph("euro", unicodes=(0x20AC,), group="symbol", traits=("symbol",))
def euro(system: System):
    # not in charset latin-1/ext-a but harmless if present; skip unicode if not needed
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); lsb = _lsb(system); ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("euro", 520))
    ring = open_bowl((lsb + w / 2, xh / 2), w / 2, xh / 2, thick=st, thin=thin, aperture=0.4, open_side="left", exponent=exp, overshoot=ov, name="bowl")
    b1 = crossbar(lsb + w * 0.05, lsb + w * 0.7, xh * 0.55, thick=thin, name="bar.1", ends="none")
    b2 = crossbar(lsb + w * 0.05, lsb + w * 0.7, xh * 0.4, thick=thin, name="bar.2", ends="none")
    return ring + b1 + b2
