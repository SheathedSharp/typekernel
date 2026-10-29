"""Superscripts and vulgar fractions (structural, slot-free)."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar, stem
from typekernel.draw import Writer, diagonal_band
from typekernel.project import glyph
from typekernel.system import System


def _lsb(system):
    return float(system.tokens.get("lsb_lc", 40.0)) * 0.4


def _small_one(system, lsb, baseline, height, width, *, tag="one"):
    st = float(system.stem["lc"]) * 0.55
    x0 = lsb + (width - st) / 2
    return stem(
        x0, x0 + st, baseline, baseline + height, name=f"stem.{tag}", foot="none", top="none"
    )


def _small_two(system, lsb, baseline, height, width, *, tag="two"):
    st = float(system.stem["lc"]) * 0.5
    # Slot-free zigzag: top bar + diagonal stem + bottom bar
    top = crossbar(
        lsb, lsb + width, baseline + height - st / 2, thick=st, name=f"bar.{tag}.t", ends="none"
    )
    bot = crossbar(
        lsb, lsb + width, baseline + st / 2, thick=st, name=f"bar.{tag}.b", ends="none"
    )
    mid = stem(
        lsb + width - st,
        lsb + width,
        baseline + st,
        baseline + height - st,
        name=f"stem.{tag}",
        foot="none",
        top="none",
    )
    return top + mid + bot


def _small_three(system, lsb, baseline, height, width, *, tag="three"):
    st = float(system.stem["lc"]) * 0.5
    top = crossbar(
        lsb, lsb + width, baseline + height - st / 2, thick=st, name=f"bar.{tag}.t", ends="none"
    )
    mid = crossbar(
        lsb + width * 0.25, lsb + width, baseline + height * 0.5, thick=st, name=f"bar.{tag}.m", ends="none"
    )
    bot = crossbar(
        lsb, lsb + width, baseline + st / 2, thick=st, name=f"bar.{tag}.b", ends="none"
    )
    spine = stem(
        lsb + width - st,
        lsb + width,
        baseline + st,
        baseline + height - st,
        name=f"stem.{tag}",
        foot="none",
        top="none",
    )
    return top + mid + bot + spine


def _small_four(system, lsb, baseline, height, width, *, tag="four"):
    st = float(system.stem["lc"]) * 0.55
    v = stem(
        lsb + width * 0.55,
        lsb + width * 0.55 + st,
        baseline,
        baseline + height,
        name=f"stem.{tag}",
        foot="none",
        top="none",
    )
    arm = stem(
        lsb,
        lsb + st,
        baseline + height * 0.35,
        baseline + height,
        name=f"stem.{tag}.arm",
        foot="none",
        top="none",
    )
    bar = crossbar(
        lsb, lsb + width, baseline + height * 0.4, thick=st * 0.85, name=f"bar.{tag}", ends="none"
    )
    return v + arm + bar


def _slash(system, lsb, w, xh, tag="slash"):
    st = float(system.stem["lc"]) * 0.55
    # Slot-free diagonal via stem at an angle? Use thin verticals approx — better a non-corner Writer
    # Use a rotated-looking pair of bars without corner slots: single stem from high-right to low-left
    # as a thick diagonal approximated by a short stem chain is hard; use Writer with .node only.
    l, r = diagonal_band(
        (lsb + w * 0.75, xh * 0.85),
        (lsb + w * 0.25, xh * 0.1),
        weight=st,
        compensate=True,
    )
    return (
        Writer()
        .start(l.start)
        .node(f"{tag}.a")
        .fragment(l)
        .node(f"{tag}.b")
        .line(r.start)
        .node(f"{tag}.c")
        .fragment(r)
        .node(f"{tag}.d")
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
    num = _small_one(system, lsb, xh * 0.55, xh * 0.4, w * 0.35, tag="num")
    den = _small_four(system, lsb + w * 0.55, 0.0, xh * 0.4, w * 0.4, tag="den")
    return num + den + _slash(system, lsb, w, xh)


@glyph("onehalf", unicodes=(0x00BD,), group="symbol", traits=("figure",))
def onehalf(system: System):
    xh = float(system.zones.x)
    lsb = _lsb(system)
    w = float(WIDTHS.get("fraction", 560))
    num = _small_one(system, lsb, xh * 0.55, xh * 0.4, w * 0.35, tag="num")
    den = _small_two(system, lsb + w * 0.55, 0.0, xh * 0.4, w * 0.4, tag="den")
    return num + den + _slash(system, lsb, w, xh)


@glyph("threequarters", unicodes=(0x00BE,), group="symbol", traits=("figure",))
def threequarters(system: System):
    xh = float(system.zones.x)
    lsb = _lsb(system)
    w = float(WIDTHS.get("fraction", 560))
    num = _small_three(system, lsb, xh * 0.55, xh * 0.4, w * 0.38, tag="num")
    den = _small_four(system, lsb + w * 0.55, 0.0, xh * 0.4, w * 0.4, tag="den")
    return num + den + _slash(system, lsb, w, xh)
