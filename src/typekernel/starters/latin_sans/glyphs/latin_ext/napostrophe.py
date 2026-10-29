"""napostrophe — n + apostrophe ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import arch, stem
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("napostrophe", unicodes=(0x0149,), group="lc.straight")
def napostrophe(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    width = float(WIDTHS.get("n", 430))
    left = stem(lsb, lsb + st, 0.0, xh, name="stem.l")
    right = stem(lsb + width - st, lsb + width, 0.0, xh, name="stem.r")
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
    # Slot-free apostrophe (nodes only — corner fillers must not run).
    ax = lsb + width + st * 0.35
    apo = (
        Writer()
        .start((ax, xh + st * 1.5))
        .node("apo.t")
        .line((ax + st * 0.55, xh + st * 1.5))
        .node("apo.tr")
        .line((ax + st * 0.35, xh + st * 0.35))
        .node("apo.b")
        .line((ax - st * 0.15, xh + st * 0.35))
        .node("apo.bl")
        .line((ax, xh + st * 1.5))
        .close()
        .build()
    )
    return zone_anchors(left + right + shoulder + apo, system, top="x")
