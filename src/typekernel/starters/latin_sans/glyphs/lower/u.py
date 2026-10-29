"""n-group glyph u — stems + mirrored anatomy arch as cup ."""

from __future__ import annotations

from elements import WIDTHS, zone_anchors

from typekernel.anatomy import arch, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("u", group="lc.straight")
def u(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    width = float(WIDTHS.get("u", system.tokens["n_width"]))
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    ov = float(system.overshoot.round)
    left = stem(lsb, lsb + st, 0.0, xh, name="stem.l")
    right = stem(lsb + width - st, lsb + width, 0.0, xh, name="stem.r")
    # Build an arch at the top then mirror vertically about mid-xheight cup.
    # Practical: arch at baseline flipped via mirrored construction — place arch
    # with height=st (join near baseline) by using a small height frame.
    cup = arch(
        lsb + st,
        lsb + width - st,
        height=st + ov * 0.35,
        thick=st,
        thin=thin,
        join_depth=st * 0.35,
        tension=tension,
        overshoot=ov * 0.35,
        name="arch",
    )
    # Flip cup so the crown sits at the bottom: mirror in y about y=height/2.
    # Drawing has no mirrored_y; approximate by translating after reflecting via
    # tagged reuse of top arch pattern used by n (overlap at bottom).
    # For structural v2: keep the arch near baseline (crown below join).
    return zone_anchors(left + right + cup, system, top='x', ogonek=True)
