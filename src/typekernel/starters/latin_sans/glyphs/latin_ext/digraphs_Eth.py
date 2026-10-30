"""Eth / eth — D/d with cross stroke (letter-class Ð/ð)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("Eth", unicodes=(0x00D0,), group="uc.round")
def Eth(system: System):
    """UC Eth ≈ D + stem stroke; one closed bowl counter (like D)."""
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("D", 680))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    ring = bowl(
        (lsb + width * 0.55, cap / 2),
        width * 0.42,
        cap / 2,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl",
    )
    # Stroke through stem only — must not open or double the D counter.
    bar = crossbar(
        lsb - st * 0.35,
        lsb + st * 1.85,
        cap * 0.55,
        thick=thin,
        name="bar",
        ends="none",
    )
    return zone_anchors(left + ring + bar, system, top="cap")


@glyph("eth", unicodes=(0x00F0,), group="lc.mixed")
def eth(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    asc = float(system.zones.asc)
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("d", 430))
    right = stem(lsb + width - st, lsb + width, 0.0, asc * 0.92, name="stem.r")
    cx = lsb + (width - st) * 0.5
    cy = xh * 0.48
    ring = bowl(
        (cx, cy),
        (width - st) * 0.55,
        xh * 0.48,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov * 0.5,
        name="bowl",
    )
    bar = crossbar(
        lsb + width * 0.15,
        lsb + width * 0.95,
        asc * 0.78,
        thick=thin,
        name="bar",
        ends="none",
    )
    return zone_anchors(ring + right + bar, system, top="x")
