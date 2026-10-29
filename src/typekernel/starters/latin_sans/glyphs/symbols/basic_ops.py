"""Basic ASCII operators and braces ."""
from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar, stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


def _lsb(system):
    return float(system.tokens.get("lsb_lc", 40.0)) * 0.45

@glyph("plus", unicodes=(0x002B,), group="symbol", traits=("symbol", "no-stem"))
def plus(system: System):
    st = float(system.stem["lc"]) * 0.85; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("plus", 420)); cy = xh * 0.48
    h = crossbar(lsb, lsb + w, cy, thick=st, name="bar.h", ends="none")
    v = stem(lsb + (w - st) / 2, lsb + (w + st) / 2, cy - w * 0.35, cy + w * 0.35, name="bar.v", foot="none", top="none")
    return h + v

@glyph("equal", unicodes=(0x003D,), group="symbol", traits=("symbol", "no-stem"))
def equal(system: System):
    st = float(system.stem["lc"]) * 0.75; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("equal", 420))
    return (crossbar(lsb, lsb + w, xh * 0.38, thick=st, name="bar.b", ends="none")
            + crossbar(lsb, lsb + w, xh * 0.58, thick=st, name="bar.t", ends="none"))

@glyph("less", unicodes=(0x003C,), group="symbol", traits=("symbol", "no-stem"))
def less(system: System):
    st = float(system.stem["lc"]) * 0.8; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("less", 400)); cy = xh * 0.5
    l1, r1 = diagonal_band((lsb + w * 0.85, cy + w * 0.35), (lsb + st, cy), weight=st, compensate=True)
    l2, r2 = diagonal_band((lsb + st, cy), (lsb + w * 0.85, cy - w * 0.35), weight=st, compensate=True)
    def band(l, r, tag):
        return (Writer().start(l.start).corner(f"{tag}.a").fragment(l).corner(f"{tag}.b")
                .line(r.start).corner(f"{tag}.c").fragment(r).corner(f"{tag}.d").line(l.start).close().build())
    return band(l1, r1, "diag.t") + band(l2, r2, "diag.b")

@glyph("greater", unicodes=(0x003E,), group="symbol", traits=("symbol", "no-stem"))
def greater(system: System):
    st = float(system.stem["lc"]) * 0.8; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("greater", 400)); cy = xh * 0.5
    l1, r1 = diagonal_band((lsb + st, cy + w * 0.35), (lsb + w - st, cy), weight=st, compensate=True)
    l2, r2 = diagonal_band((lsb + w - st, cy), (lsb + st, cy - w * 0.35), weight=st, compensate=True)
    def band(l, r, tag):
        return (Writer().start(l.start).corner(f"{tag}.a").fragment(l).corner(f"{tag}.b")
                .line(r.start).corner(f"{tag}.c").fragment(r).corner(f"{tag}.d").line(l.start).close().build())
    return band(l1, r1, "diag.t") + band(l2, r2, "diag.b")

@glyph("asterisk", unicodes=(0x002A,), group="symbol", traits=("symbol", "no-stem"))
def asterisk(system: System):
    st = float(system.stem["lc"]) * 0.55; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("asterisk", 360)); cx = lsb + w / 2; cy = xh * 0.62; r = w * 0.28
    parts = []
    for i, (dx, dy) in enumerate([(0, 1), (0.87, 0.5), (0.87, -0.5), (0, -1), (-0.87, -0.5), (-0.87, 0.5)]):
        l, rr = diagonal_band((cx + dx * r * 0.2, cy + dy * r * 0.2), (cx + dx * r, cy + dy * r), weight=st, compensate=False)
        parts.append(Writer().start(l.start).corner(f"ray.{i}.a").fragment(l).corner(f"ray.{i}.b")
                     .line(rr.start).corner(f"ray.{i}.c").fragment(rr).corner(f"ray.{i}.d").line(l.start).close().build())
    out = parts[0]
    for p in parts[1:]:
        out = out + p
    return out

@glyph("numbersign", unicodes=(0x0023,), group="symbol", traits=("symbol", "no-stem"))
def numbersign(system: System):
    st = float(system.stem["lc"]) * 0.7; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("numbersign", 480))
    h1 = crossbar(lsb, lsb + w, xh * 0.38, thick=st, name="bar.b", ends="none")
    h2 = crossbar(lsb, lsb + w, xh * 0.58, thick=st, name="bar.t", ends="none")
    v1 = stem(lsb + w * 0.28, lsb + w * 0.28 + st, xh * 0.15, xh * 0.85, name="stem.l", foot="none", top="none")
    v2 = stem(lsb + w * 0.62, lsb + w * 0.62 + st, xh * 0.15, xh * 0.85, name="stem.r", foot="none", top="none")
    return h1 + h2 + v1 + v2

@glyph("at", unicodes=(0x0040,), group="symbol", traits=("symbol",))
def at(system: System):
    st = float(system.stem["lc"]) * 0.7; thin = st * 0.85
    xh = float(system.zones.x); lsb = _lsb(system); ov = float(system.overshoot.round)
    from typekernel.anatomy import bowl, open_bowl
    w = float(WIDTHS.get("at", 700)); exp = float(system.tokens.get("bowl_exponent", 2.15))
    outer = open_bowl((lsb + w / 2, xh * 0.48), w / 2, xh * 0.48, thick=st, thin=thin, aperture=0.22, open_side="right", exponent=exp, overshoot=ov, name="bowl.o")
    inner = bowl((lsb + w / 2, xh * 0.48), w * 0.22, xh * 0.22, thick=st * 0.85, thin=thin * 0.85, exponent=exp, name="bowl.i")
    return outer + inner

@glyph("asciicircum", unicodes=(0x005E,), group="symbol", traits=("symbol", "no-stem"))
def asciicircum(system: System):
    st = float(system.stem["lc"]) * 0.7; xh = float(system.zones.x); lsb = _lsb(system)
    from typekernel.anatomy import diagonal_pair
    w = float(WIDTHS.get("asciicircum", 360))
    return diagonal_pair((lsb + w / 2, xh * 0.95), (lsb, xh * 0.55), (lsb + w, xh * 0.55), weight=st, name="diag")

@glyph("underscore", unicodes=(0x005F,), group="symbol", traits=("symbol", "no-stem"))
def underscore(system: System):
    st = float(system.stem["lc"]) * 0.7; lsb = _lsb(system)
    w = float(WIDTHS.get("underscore", 480))
    return crossbar(lsb, lsb + w, -st * 0.2, thick=st, name="bar", ends="none")

@glyph("bar", unicodes=(0x007C,), group="symbol", traits=("symbol", "no-stem"))
def bar(system: System):
    st = float(system.stem["lc"]) * 0.75; asc = float(system.zones.asc); desc = float(system.zones.desc)
    lsb = _lsb(system); w = float(WIDTHS.get("bar", 200))
    x0 = lsb + (w - st) / 2
    return stem(x0, x0 + st, desc * 0.3, asc * 0.9, name="stem", foot="none", top="none")

@glyph("brokenbar", unicodes=(0x00A6,), group="symbol", traits=("symbol", "no-stem"))
def brokenbar(system: System):
    st = float(system.stem["lc"]) * 0.75; asc = float(system.zones.asc); desc = float(system.zones.desc)
    xh = float(system.zones.x); lsb = _lsb(system); w = float(WIDTHS.get("bar", 200))
    x0 = lsb + (w - st) / 2; gap = st * 0.8
    return (stem(x0, x0 + st, desc * 0.3, xh * 0.45 - gap / 2, name="stem.b", foot="none", top="none")
            + stem(x0, x0 + st, xh * 0.45 + gap / 2, asc * 0.9, name="stem.t", foot="none", top="none"))


@glyph("braceleft", unicodes=(0x007B,), group="punct", traits=("punct", "no-stem"))
def braceleft(system: System):
    st = float(system.stem["lc"]) * 0.7; asc = float(system.zones.asc); desc = float(system.zones.desc)
    lsb = _lsb(system); w = float(WIDTHS.get("brace", 280)); mid = (asc + desc) / 2
    # Slot-free construction: verticals + bars (no corner fillers).
    outer = stem(lsb + w * 0.55, lsb + w * 0.55 + st, desc * 0.2, asc * 0.9, name="stem.o", foot="none", top="none")
    tip = stem(lsb + w * 0.15, lsb + w * 0.15 + st, mid - st * 0.6, mid + st * 0.6, name="stem.tip", foot="none", top="none")
    top = crossbar(lsb + w * 0.15, lsb + w * 0.55 + st, asc * 0.9 - st / 2, thick=st, name="bar.t", ends="none")
    bot = crossbar(lsb + w * 0.15, lsb + w * 0.55 + st, desc * 0.2 + st / 2, thick=st, name="bar.b", ends="none")
    midb = crossbar(lsb + w * 0.15, lsb + w * 0.55, mid, thick=st, name="bar.m", ends="none")
    return outer + tip + top + bot + midb

@glyph("braceright", unicodes=(0x007D,), group="punct", traits=("punct", "no-stem"))
def braceright(system: System):
    st = float(system.stem["lc"]) * 0.7; asc = float(system.zones.asc); desc = float(system.zones.desc)
    lsb = _lsb(system); w = float(WIDTHS.get("brace", 280)); mid = (asc + desc) / 2
    outer = stem(lsb + w * 0.3, lsb + w * 0.3 + st, desc * 0.2, asc * 0.9, name="stem.o", foot="none", top="none")
    tip = stem(lsb + w * 0.7, lsb + w * 0.7 + st, mid - st * 0.6, mid + st * 0.6, name="stem.tip", foot="none", top="none")
    top = crossbar(lsb + w * 0.3, lsb + w * 0.7 + st, asc * 0.9 - st / 2, thick=st, name="bar.t", ends="none")
    bot = crossbar(lsb + w * 0.3, lsb + w * 0.7 + st, desc * 0.2 + st / 2, thick=st, name="bar.b", ends="none")
    midb = crossbar(lsb + w * 0.3 + st, lsb + w * 0.7 + st, mid, thick=st, name="bar.m", ends="none")
    return outer + tip + top + bot + midb

@glyph("asciitilde", unicodes=(0x007E,), group="symbol", traits=("symbol", "no-stem"))
def asciitilde(system: System):
    st = float(system.stem["lc"]) * 0.55; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("asciitilde", 420)); y = xh * 0.55; amp = st * 1.1
    return (Writer().start((lsb, y)).corner("bar.l")
            .curve((lsb + w * 0.25, y + amp), (lsb + w * 0.75, y - amp), (lsb + w, y))
            .corner("bar.r").line((lsb + w, y - st)).corner("bar.r.b")
            .curve((lsb + w * 0.75, y - amp - st), (lsb + w * 0.25, y + amp - st), (lsb, y - st))
            .corner("bar.l.b").line((lsb, y)).close().build())
