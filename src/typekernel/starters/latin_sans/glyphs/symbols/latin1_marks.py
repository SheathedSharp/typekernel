"""Latin-1 spacing accents, guillemets, ordinals, etc. ."""
from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import bowl, crossbar, diagonal_pair, dot, drop, stem
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


def _lsb(system):
    return float(system.tokens.get("lsb_lc", 40.0)) * 0.5

@glyph("grave", unicodes=(0x0060,), group="spacing_marks", traits=("spacing-mark",))
def grave(system: System):
    st = float(system.stem["lc"]) * 0.55; h = st * 2.0; lsb = _lsb(system)
    body = drop((lsb + st * 0.2, h + st), (lsb + st * 0.9, st * 0.4), width=st * 0.85, name="drop")
    return body

@glyph("acute", unicodes=(0x00B4,), group="spacing_marks", traits=("spacing-mark",))
def acute(system: System):
    st = float(system.stem["lc"]) * 0.55; h = st * 2.0; lsb = _lsb(system)
    body = drop((lsb + st * 1.2, h + st), (lsb + st * 0.5, st * 0.4), width=st * 0.85, name="drop")
    return body

@glyph("dieresis", unicodes=(0x00A8,), group="spacing_marks", traits=("spacing-mark",))
def dieresis(system: System):
    st = float(system.stem["lc"]); diam = st * 0.85; lsb = _lsb(system); gap = st * 0.55
    y = diam / 2 + st * 0.4; cx = lsb + diam + gap
    return dot((cx - gap, y), diam, name="dot.l") + dot((cx + gap, y), diam, name="dot.r")

@glyph("macron", unicodes=(0x00AF,), group="spacing_marks", traits=("spacing-mark",))
def macron(system: System):
    st = float(system.stem["lc"]) * 0.4; lsb = _lsb(system); w = st * 3.2
    return crossbar(lsb, lsb + w, st * 1.2, thick=st, name="bar", ends="none")

@glyph("cedilla", unicodes=(0x00B8,), group="spacing_marks", traits=("spacing-mark",))
def cedilla(system: System):
    st = float(system.stem["lc"]) * 0.55; lsb = _lsb(system)
    return drop((lsb + st, -st * 0.1), (lsb + st, -st * 2.3), width=st * 1.05, name="drop")

@glyph("degree", unicodes=(0x00B0,), group="symbol", traits=("symbol", "no-stem"))
def degree(system: System):
    st = float(system.stem["lc"]) * 0.4; xh = float(system.zones.x); lsb = _lsb(system)
    r = st * 1.2
    return bowl((lsb + r + st, xh * 0.85), r, r, thick=st, thin=st * 0.9, name="bowl")

@glyph("periodcentered", unicodes=(0x00B7,), group="punct", traits=("punct", "no-stem"))
def periodcentered(system: System):
    st = float(system.stem["lc"]); xh = float(system.zones.x); lsb = _lsb(system)
    return dot((lsb + st, xh * 0.5), st * 0.95, shape="square", name="dot")

@glyph("guillemotleft", unicodes=(0x00AB,), group="punct", traits=("punct", "no-stem"))
def guillemotleft(system: System):
    st = float(system.stem["lc"]) * 0.7; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("guillemet", 420)); cy = xh * 0.5
    a = diagonal_pair((lsb + w * 0.38, cy), (lsb + w * 0.08, cy + w * 0.28), (lsb + w * 0.08, cy - w * 0.28), weight=st, name="diag.l")
    b = diagonal_pair((lsb + w * 0.78, cy), (lsb + w * 0.48, cy + w * 0.28), (lsb + w * 0.48, cy - w * 0.28), weight=st, name="diag.r")
    return a + b

@glyph("guillemotright", unicodes=(0x00BB,), group="punct", traits=("punct", "no-stem"))
def guillemotright(system: System):
    st = float(system.stem["lc"]) * 0.7; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("guillemet", 420)); cy = xh * 0.5
    a = diagonal_pair((lsb + w * 0.22, cy), (lsb + w * 0.52, cy + w * 0.28), (lsb + w * 0.52, cy - w * 0.28), weight=st, name="diag.l")
    b = diagonal_pair((lsb + w * 0.62, cy), (lsb + w * 0.92, cy + w * 0.28), (lsb + w * 0.92, cy - w * 0.28), weight=st, name="diag.r")
    return a + b

@glyph("exclamdown", unicodes=(0x00A1,), group="punct", traits=("punct",))
def exclamdown(system: System):
    st = float(system.stem["lc"]); xh = float(system.zones.x); lsb = _lsb(system)
    from typekernel.anatomy import stem as stem_part
    w = float(WIDTHS.get("exclam", 200)); x0 = lsb + (w - st) / 2
    body = stem_part(x0, x0 + st, xh * 0.2, xh * 0.85, name="stem", foot="none", top="none")
    tittle = dot((x0 + st / 2, st * 0.55), st * 0.95, shape="square", name="dot")
    return body + tittle

@glyph("questiondown", unicodes=(0x00BF,), group="punct", traits=("punct",))
def questiondown(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); lsb = _lsb(system); ov = float(system.overshoot.round)
    from typekernel.anatomy import open_bowl
    from typekernel.anatomy import stem as stem_part
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("question", 320))
    # inverted question: bowl at bottom-ish + stem + dot on top
    bowl_y = xh * 0.35
    ring = open_bowl((lsb + w / 2, bowl_y), w * 0.42, xh * 0.32, thick=st, thin=thin, aperture=0.4, open_side="left", exponent=exp, overshoot=ov * 0.3, name="bowl")
    x0 = lsb + (w - st) / 2
    spine = stem_part(x0, x0 + st, bowl_y + xh * 0.15, xh * 0.75, name="stem", foot="none", top="none")
    tittle = dot((x0 + st / 2, xh * 0.9), st * 0.9, shape="square", name="dot")
    return ring + spine + tittle

@glyph("ordfeminine", unicodes=(0x00AA,), group="symbol", traits=("symbol",))
def ordfeminine(system: System):
    st = float(system.stem["lc"]) * 0.7; thin = st * 0.85; xh = float(system.zones.x); lsb = _lsb(system)
    from typekernel.anatomy import bowl
    from typekernel.anatomy import stem as stem_part
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("ord", 280))
    # small a raised
    y0 = xh * 0.45; h = xh * 0.5
    right = stem_part(lsb + w - st, lsb + w, y0, y0 + h, name="stem.r")
    ring = bowl((lsb + w * 0.4, y0 + h * 0.48), w * 0.35, h * 0.48, thick=st, thin=thin, exponent=exp, name="bowl")
    return ring + right

@glyph("ordmasculine", unicodes=(0x00BA,), group="symbol", traits=("symbol",))
def ordmasculine(system: System):
    st = float(system.stem["lc"]) * 0.7; thin = st * 0.85; xh = float(system.zones.x); lsb = _lsb(system)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("ord", 280))
    y0 = xh * 0.45; h = xh * 0.5
    return bowl((lsb + w / 2, y0 + h / 2), w * 0.4, h * 0.48, thick=st, thin=thin, exponent=exp, name="bowl")

@glyph("logicalnot", unicodes=(0x00AC,), group="symbol", traits=("symbol", "no-stem"))
def logicalnot(system: System):
    st = float(system.stem["lc"]) * 0.75; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("logicalnot", 420))
    return (crossbar(lsb, lsb + w, xh * 0.55, thick=st, name="bar.h", ends="none")
            + stem(lsb + w - st, lsb + w, xh * 0.25, xh * 0.55, name="bar.v", foot="none", top="none"))

@glyph("plusminus", unicodes=(0x00B1,), group="symbol", traits=("symbol", "no-stem"))
def plusminus(system: System):
    st = float(system.stem["lc"]) * 0.8; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("plus", 420)); cy = xh * 0.58
    h = crossbar(lsb, lsb + w, cy, thick=st, name="bar.h", ends="none")
    v = stem(lsb + (w - st) / 2, lsb + (w + st) / 2, cy - w * 0.28, cy + w * 0.28, name="bar.v", foot="none", top="none")
    m = crossbar(lsb, lsb + w, xh * 0.28, thick=st, name="bar.m", ends="none")
    return h + v + m

@glyph("multiply", unicodes=(0x00D7,), group="symbol", traits=("symbol", "no-stem"))
def multiply(system: System):
    st = float(system.stem["lc"]) * 0.75; xh = float(system.zones.x); lsb = _lsb(system)
    from typekernel.draw import diagonal_band
    w = float(WIDTHS.get("multiply", 400)); cy = xh * 0.5
    l1, r1 = diagonal_band((lsb + st, cy + w * 0.32), (lsb + w - st, cy - w * 0.32), weight=st, compensate=True)
    l2, r2 = diagonal_band((lsb + st, cy - w * 0.32), (lsb + w - st, cy + w * 0.32), weight=st, compensate=True)
    def band(l, r, tag):
        return (Writer().start(l.start).corner(f"{tag}.a").fragment(l).corner(f"{tag}.b")
                .line(r.start).corner(f"{tag}.c").fragment(r).corner(f"{tag}.d").line(l.start).close().build())
    return band(l1, r1, "diag.a") + band(l2, r2, "diag.b")

@glyph("divide", unicodes=(0x00F7,), group="symbol", traits=("symbol", "no-stem"))
def divide(system: System):
    st = float(system.stem["lc"]) * 0.75; xh = float(system.zones.x); lsb = _lsb(system)
    w = float(WIDTHS.get("divide", 420))
    bar = crossbar(lsb, lsb + w, xh * 0.5, thick=st, name="bar", ends="none")
    d1 = dot((lsb + w / 2, xh * 0.72), st * 0.9, name="dot.t")
    d2 = dot((lsb + w / 2, xh * 0.28), st * 0.9, name="dot.b")
    return bar + d1 + d2

@glyph("section", unicodes=(0x00A7,), group="symbol", traits=("symbol",))
def section(system: System):
    st = float(system.stem["lc"]) * 0.75; thin = st * 0.85; xh = float(system.zones.x); lsb = _lsb(system)
    from typekernel.anatomy import open_bowl
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("section", 400))
    top = open_bowl((lsb + w / 2, xh * 0.7), w * 0.38, xh * 0.28, thick=st, thin=thin, aperture=0.5, open_side="left", exponent=exp, name="bowl.t")
    bot = open_bowl((lsb + w / 2, xh * 0.3), w * 0.38, xh * 0.28, thick=st, thin=thin, aperture=0.5, open_side="right", exponent=exp, name="bowl.b")
    return top + bot

@glyph("paragraph", unicodes=(0x00B6,), group="symbol", traits=("symbol",))
def paragraph(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); asc = float(system.zones.asc); lsb = _lsb(system)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("paragraph", 480))
    ring = bowl((lsb + w * 0.38, xh * 0.65), w * 0.28, xh * 0.28, thick=st, thin=thin, exponent=exp, name="bowl")
    s1 = stem(lsb + w * 0.55, lsb + w * 0.55 + st * 0.85, xh * 0.15, asc * 0.9, name="stem.a", foot="none", top="none")
    s2 = stem(lsb + w * 0.72, lsb + w * 0.72 + st * 0.85, xh * 0.15, asc * 0.9, name="stem.b", foot="none", top="none")
    return ring + s1 + s2

@glyph("copyright", unicodes=(0x00A9,), group="symbol", traits=("symbol",))
def copyright(system: System):
    st = float(system.stem["lc"]) * 0.65; thin = st * 0.9; xh = float(system.zones.x); lsb = _lsb(system)
    from typekernel.anatomy import open_bowl
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("copyright", 640)); ov = float(system.overshoot.round)
    outer = bowl((lsb + w / 2, xh / 2), w / 2, xh / 2, thick=st, thin=thin, exponent=exp, overshoot=ov * 0.3, name="bowl.o")
    inner = open_bowl((lsb + w / 2, xh / 2), w * 0.22, xh * 0.22, thick=st * 0.9, thin=thin * 0.9, aperture=0.4, open_side="right", exponent=exp, name="bowl.c")
    return outer + inner

@glyph("registered", unicodes=(0x00AE,), group="symbol", traits=("symbol",))
def registered(system: System):
    st = float(system.stem["lc"]) * 0.65; thin = st * 0.9; xh = float(system.zones.x); lsb = _lsb(system)
    exp = float(system.tokens.get("bowl_exponent", 2.15)); w = float(WIDTHS.get("copyright", 640)); ov = float(system.overshoot.round)
    outer = bowl((lsb + w / 2, xh / 2), w / 2, xh / 2, thick=st, thin=thin, exponent=exp, overshoot=ov * 0.3, name="bowl.o")
    # small R: stem + bowl
    cx = lsb + w / 2; cy = xh / 2
    rs = stem(cx - w * 0.12, cx - w * 0.12 + st * 0.8, cy - xh * 0.22, cy + xh * 0.22, name="stem", foot="none", top="none")
    rb = bowl((cx + w * 0.02, cy + xh * 0.08), w * 0.12, xh * 0.1, thick=st * 0.8, thin=thin * 0.8, exponent=exp, name="bowl.r")
    return outer + rs + rb

@glyph("mu", unicodes=(0x00B5,), group="lc.mixed")
def mu(system: System):
    st = float(system.stem["lc"]); thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x); desc = float(system.zones.desc); lsb = float(system.tokens.get("lsb_lc", 40.0))
    width = float(WIDTHS.get("u", 430))
    left = stem(lsb, lsb + st, desc * 0.2, xh, name="stem.l")
    right = stem(lsb + width - st, lsb + width, 0.0, xh, name="stem.r")
    # u arch at bottom
    # use inverted feel via bowl trough — approximate with two stems + bottom connection via Writer
    bot = (Writer().start((lsb + st, st * 0.2)).corner("arch.l")
           .curve((lsb + st, -st * 0.1), (lsb + width - st, -st * 0.1), (lsb + width - st, st * 0.2))
           .corner("arch.r").line((lsb + width - st * 0.15, st * 0.2 + thin))
           .corner("arch.ri")
           .curve((lsb + width - st, thin * 1.2), (lsb + st, thin * 1.2), (lsb + st * 0.15, st * 0.2 + thin))
           .corner("arch.li").line((lsb + st, st * 0.2)).close().build())
    return left + right + bot
