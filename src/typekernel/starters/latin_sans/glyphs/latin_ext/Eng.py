"""Eng / eng — N/n with descender . Slot/signature-stable."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import arch, crossbar, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("Eng", unicodes=(0x014A,), group="uc.straight")
def Eng(system: System):
    st = float(system.stem["uc"])
    thin = float(system.stem.get("uc_h", st * 0.85))
    cap = float(system.zones.cap)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    width = float(WIDTHS.get("N", 700))
    left = stem(lsb, lsb + st, 0.0, cap, name="stem.l")
    right = stem(lsb + width - st, lsb + width, desc + st, cap, name="stem.r")
    # Diagonal as two bars approximation for stable signature across masters
    diag = crossbar(
        lsb + st * 0.3,
        lsb + width - st * 0.3,
        cap * 0.5,
        thick=st * 0.85,
        name="bar.diag",
        ends="none",
    )
    hook_bar = crossbar(
        lsb + width * 0.45,
        lsb + width,
        desc + st * 1.2,
        thick=thin,
        name="bar.hook",
        ends="none",
    )
    return zone_anchors(left + right + diag + hook_bar, system, top="cap")


@glyph("eng", unicodes=(0x014B,), group="lc.straight")
def eng(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    width = float(WIDTHS.get("n", 430))
    left = stem(lsb, lsb + st, 0.0, xh, name="stem.l")
    right = stem(lsb + width - st, lsb + width, desc + st, xh, name="stem.r")
    shoulder = arch(
        lsb + st,
        lsb + width - st,
        height=xh,
        thick=st,
        thin=thin,
        join_depth=st * 0.55,
        tension=0.55,
        name="arch",
    )
    hook_bar = crossbar(
        lsb + width * 0.4,
        lsb + width,
        desc + st * 1.1,
        thick=thin,
        name="bar.hook",
        ends="none",
    )
    return zone_anchors(left + right + shoulder + hook_bar, system, top="x")
