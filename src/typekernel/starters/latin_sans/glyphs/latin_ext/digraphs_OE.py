"""OE / oe digraphs — two overlapping bowls (2 counters, master-stable)."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("OE", unicodes=(0x0152,), group="uc.round")
def OE(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("OE", 980))
    bowl_w = width * 0.52
    left = bowl(
        (lsb + bowl_w / 2, cap / 2),
        bowl_w / 2,
        cap / 2,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.l",
    )
    bridge = stem(
        lsb + bowl_w - st * 0.4,
        lsb + bowl_w + st * 0.4,
        0.0,
        cap,
        name="stem",
        foot="none",
        top="none",
    )
    cx = lsb + bowl_w + (width - bowl_w) * 0.45 - st * 0.25
    rx = (width - bowl_w) * 0.48
    right = bowl(
        (cx, cap / 2),
        rx,
        cap / 2,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.r",
    )
    # Light E cue that does not change counter count across masters.
    mid = crossbar(
        cx - rx * 0.2,
        lsb + width - st * 0.2,
        cap * 0.5,
        thick=thin,
        name="bar.1",
        ends="none",
    )
    return zone_anchors(left + bridge + right + mid, system, top="cap")


@glyph("oe", unicodes=(0x0153,), group="lc.round")
def oe(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("oe", 720))
    left_w = width * 0.50
    left = bowl(
        (lsb + left_w / 2, xh / 2),
        left_w / 2,
        xh / 2,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.l",
    )
    cx = lsb + left_w + (width - left_w) * 0.45 - st * 0.2
    rx = (width - left_w) * 0.48
    right = bowl(
        (cx, xh / 2),
        rx,
        xh / 2,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov,
        name="bowl.r",
    )
    return zone_anchors(left + right, system, top="x")
