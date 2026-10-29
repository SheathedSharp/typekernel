"""Superscripts and vulgar fractions (structural, slot-free)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar, stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


def _lsb(system):
    return float(system.tokens.get("lsb_lc", 40.0)) * 0.4


def _small_one(system, lsb, baseline, height, width, *, idx: str = ""):
    st = float(system.stem["lc"]) * 0.55
    x0 = lsb + (width - st) / 2
    n = f"stem.{idx}" if idx else "stem"
    return stem(
        x0, x0 + st, baseline, baseline + height, name=n, foot="none", top="none"
    )


def _small_two(system, lsb, baseline, height, width, *, idx: str = ""):
    st = float(system.stem["lc"]) * 0.5
    # Slot-free zigzag: top bar + diagonal stem + bottom bar
    bt = f"bar.{idx}.t" if idx else "bar.t"
    bb = f"bar.{idx}.b" if idx else "bar.b"
    sn = f"stem.{idx}" if idx else "stem"
    top = crossbar(
        lsb, lsb + width, baseline + height - st / 2, thick=st, name=bt, ends="none"
    )
    bot = crossbar(
        lsb, lsb + width, baseline + st / 2, thick=st, name=bb, ends="none"
    )
    mid = stem(
        lsb + width - st,
        lsb + width,
        baseline + st,
        baseline + height - st,
        name=sn,
        foot="none",
        top="none",
    )
    return top + mid + bot


def _small_three(system, lsb, baseline, height, width, *, idx: str = ""):
    st = float(system.stem["lc"]) * 0.5
    bt = f"bar.{idx}.t" if idx else "bar.t"
    bm = f"bar.{idx}.1" if idx else "bar.1"
    bb = f"bar.{idx}.b" if idx else "bar.b"
    sn = f"stem.{idx}" if idx else "stem"
    top = crossbar(
        lsb, lsb + width, baseline + height - st / 2, thick=st, name=bt, ends="none"
    )
    mid = crossbar(
        lsb + width * 0.25, lsb + width, baseline + height * 0.5, thick=st, name=bm, ends="none"
    )
    bot = crossbar(
        lsb, lsb + width, baseline + st / 2, thick=st, name=bb, ends="none"
    )
    spine = stem(
        lsb + width - st,
        lsb + width,
        baseline + st,
        baseline + height - st,
        name=sn,
        foot="none",
        top="none",
    )
    return top + mid + bot + spine


def _small_four(system, lsb, baseline, height, width, *, idx: str = ""):
    st = float(system.stem["lc"]) * 0.55
    sn = f"stem.{idx}" if idx else "stem"
    s1 = f"stem.{idx}1" if idx else "stem.1"
    # if idx="2", stem.21 is weird — use stem.2 / stem.3 for den arms
    if idx:
        sn, s1 = f"stem.{idx}", f"stem.{int(idx)+1}"
    bn = f"bar.{idx}" if idx else "bar"
    v = stem(
        lsb + width * 0.55,
        lsb + width * 0.55 + st,
        baseline,
        baseline + height,
        name=sn,
        foot="none",
        top="none",
    )
    arm = stem(
        lsb,
        lsb + st,
        baseline + height * 0.35,
        baseline + height,
        name=s1,
        foot="none",
        top="none",
    )
    bar = crossbar(
        lsb, lsb + width, baseline + height * 0.4, thick=st * 0.85, name=bn, ends="none"
    )
    return v + arm + bar


def _slash(system, lsb, w, xh):
    st = float(system.stem["lc"]) * 0.55
    l, r = diagonal_band(
        (lsb + w * 0.75, xh * 0.85),
        (lsb + w * 0.25, xh * 0.1),
        weight=st,
        compensate=True,
    )
    return (
        Writer()
        .start(l.start)
        .node("diag.l.a")
        .fragment(l)
        .node("diag.l.b")
        .line(r.start)
        .node("diag.r.a")
        .fragment(r)
        .node("diag.r.b")
        .line(l.start)
        .close()
        .build()
    )


@glyph("onesuperior", unicodes=(0x00B9,), group="symbol", traits=("figure", "no-stem"))
def onesuperior(system: System):
    xh = float(system.zones.x)
    lsb = _lsb(system)
    w = float(WIDTHS.get("sup", 220))
    return _small_one(system, lsb, xh * 0.55, xh * 0.45, w)


@glyph("twosuperior", unicodes=(0x00B2,), group="symbol", traits=("figure", "no-stem"))
def twosuperior(system: System):
    xh = float(system.zones.x)
    lsb = _lsb(system)
    w = float(WIDTHS.get("sup", 220))
    return _small_two(system, lsb, xh * 0.55, xh * 0.45, w)


@glyph("threesuperior", unicodes=(0x00B3,), group="symbol", traits=("figure", "no-stem"))
def threesuperior(system: System):
    xh = float(system.zones.x)
    lsb = _lsb(system)
    w = float(WIDTHS.get("sup", 220))
    return _small_three(system, lsb, xh * 0.55, xh * 0.45, w)


@glyph("onequarter", unicodes=(0x00BC,), group="symbol", traits=("figure",))
def onequarter(system: System):
    xh = float(system.zones.x)
    lsb = _lsb(system)
    w = float(WIDTHS.get("fraction", 560))
    num = _small_one(system, lsb, xh * 0.55, xh * 0.4, w * 0.35, idx="1")
    den = _small_four(system, lsb + w * 0.55, 0.0, xh * 0.4, w * 0.4, idx="2")
    return num + den + _slash(system, lsb, w, xh)


@glyph("onehalf", unicodes=(0x00BD,), group="symbol", traits=("figure",))
def onehalf(system: System):
    xh = float(system.zones.x)
    lsb = _lsb(system)
    w = float(WIDTHS.get("fraction", 560))
    num = _small_one(system, lsb, xh * 0.55, xh * 0.4, w * 0.35, idx="1")
    den = _small_two(system, lsb + w * 0.55, 0.0, xh * 0.4, w * 0.4, idx="2")
    return num + den + _slash(system, lsb, w, xh)


@glyph("threequarters", unicodes=(0x00BE,), group="symbol", traits=("figure",))
def threequarters(system: System):
    xh = float(system.zones.x)
    lsb = _lsb(system)
    w = float(WIDTHS.get("fraction", 560))
    num = _small_three(system, lsb, xh * 0.55, xh * 0.4, w * 0.38, idx="1")
    den = _small_four(system, lsb + w * 0.55, 0.0, xh * 0.4, w * 0.4, idx="3")
    return num + den + _slash(system, lsb, w, xh)
