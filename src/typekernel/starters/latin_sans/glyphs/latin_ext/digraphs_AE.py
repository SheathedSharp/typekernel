"""AE / ae digraphs . Paired file — macOS case-insensitive FS."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import bowl, crossbar, diagonal_pair, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("AE", unicodes=(0x00C6,), group="uc.mixed")
def AE(system: System):
    """UC digraph — A triangle + E bars (letter-class Æ).

    One closed A counter; open E (top/mid/bot bars). Topology target 1/1,
    master-stable under wght lerp.
    """
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    width = float(WIDTHS.get("AE", 920))
    # Left A occupies ~55%; right E stem sits on the A mid-leg.
    a_w = width * 0.55
    apex = (lsb + a_w * 0.42, cap)
    left_foot = (lsb + st * 0.2, 0.0)
    mid_foot = (lsb + a_w - st * 0.15, 0.0)
    legs = diagonal_pair(apex, left_foot, mid_foot, weight=st, name="diag")
    abar = crossbar(
        lsb + a_w * 0.16,
        lsb + a_w * 0.82,
        cap * 0.38,
        thick=thin,
        name="bar.a",
        ends="none",
    )
    stem_x0 = lsb + a_w - st * 0.55
    right = stem(stem_x0, stem_x0 + st, 0.0, cap, name="stem.r")
    e_right = lsb + width
    top = crossbar(
        stem_x0 + st * 0.45,
        e_right,
        cap - thin / 2.0,
        thick=thin,
        name="bar.t",
        ends="none",
    )
    mid = crossbar(
        stem_x0 + st * 0.45,
        e_right - st * 0.2,
        cap * 0.5,
        thick=thin,
        name="bar.1",
        ends="none",
    )
    bot = crossbar(
        stem_x0 + st * 0.45,
        e_right,
        thin / 2.0,
        thick=thin,
        name="bar.b",
        ends="none",
    )
    return zone_anchors(
        legs + abar + right + top + mid + bot, system, top="cap"
    )


@glyph("ae", unicodes=(0x00E6,), group="lc.mixed")
def ae(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    ov = float(system.overshoot.round)
    exp = float(system.tokens.get("bowl_exponent", 2.15))
    width = float(WIDTHS.get("ae", 700))
    stem_x0 = lsb + width * 0.42
    right_stem = stem(stem_x0, stem_x0 + st, 0.0, xh, name="stem")
    cx_l = lsb + (stem_x0 - lsb) * 0.55
    left = bowl(
        (cx_l, xh * 0.48),
        (stem_x0 - lsb) * 0.55,
        xh * 0.48,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov * 0.4,
        name="bowl.l",
    )
    cx_r = stem_x0 + st + (lsb + width - stem_x0 - st) * 0.5 - st * 0.3
    rx = (lsb + width - stem_x0 - st) * 0.52
    right = bowl(
        (cx_r, xh * 0.48),
        rx,
        xh * 0.48,
        thick=st,
        thin=thin,
        exponent=exp,
        overshoot=ov * 0.4,
        name="bowl.r",
    )
    return zone_anchors(left + right_stem + right, system, top="x")
