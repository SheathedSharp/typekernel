"""IJ / ij — side-by-side I+J / i+j ."""
from __future__ import annotations

from elements import WIDTHS, arch_span, zone_anchors

from typekernel.anatomy import stem
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("IJ", unicodes=(0x0132,), group="uc.straight")
def IJ(system: System):
    st = float(system.stem["uc"]); cap = float(system.zones.cap); desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    i_w = float(WIDTHS.get("I", 220)); j_w = float(WIDTHS.get("J", 520))
    i_body = stem(lsb, lsb + st, 0.0, cap, name="stem.i")
    j_x0 = lsb + i_w
    j_stem = stem(j_x0 + (j_w - st) * 0.55, j_x0 + (j_w - st) * 0.55 + st, desc * 0.25, cap, name="stem.1")
    # simple J hook via arch_span trough
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    x0 = j_x0 + (j_w - st) * 0.55
    hook_y = desc * 0.3
    outer = arch_span(x0 + st, hook_y, x0 - j_w * 0.35, desc + st * 0.3, desc - 2.0, tension=tension)
    inner = arch_span(x0 - j_w * 0.35 + st * 0.7, desc + st, x0, hook_y, desc + st * 1.2, tension=tension)
    curl = (Writer().start((x0, hook_y)).corner("hook.entry").line((x0 + st, hook_y)).corner("hook.exit")
            .fragment(outer).corner("hook.apex").line((x0 - j_w * 0.35 + st * 0.7, desc + st))
            .corner("hook.stress").fragment(inner).close().build())
    return zone_anchors(i_body + j_stem + curl, system, top="cap")

@glyph("ij", unicodes=(0x0133,), group="lc.straight")
def ij(system: System):
    st = float(system.stem["lc"]); xh = float(system.zones.x); desc = float(system.zones.desc)
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    from typekernel.anatomy import dot
    i_w = float(WIDTHS.get("i", 180)); j_w = float(WIDTHS.get("j", 220))
    ix = lsb + (i_w - st) / 2
    i_body = stem(ix, ix + st, 0.0, xh, name="stem.i")
    di = st * 1.05; tittle_i = dot((ix + st / 2, xh + di * 0.7), di, name="dot.i")
    jx = lsb + i_w + (j_w - st) / 2
    hook_y = desc + st * 1.1
    j_body = stem(jx, jx + st, hook_y, xh, name="stem.1")
    tittle_j = dot((jx + st / 2, xh + di * 0.7), di, name="dot")
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    x_l = jx + st - j_w * 0.85
    outer = arch_span(jx + st, hook_y, x_l, desc + st * 0.2, desc - 4.0, tension=tension)
    inner = arch_span(x_l + st * 0.7, desc + st * 0.85, jx, hook_y, desc + st * 1.35, tension=tension)
    curl = (Writer().start((jx, hook_y)).corner("hook.entry").line((jx + st, hook_y)).corner("hook.exit")
            .fragment(outer).corner("hook.apex").line((x_l + st * 0.7, desc + st * 0.85))
            .corner("hook.stress").fragment(inner).close().build())
    return zone_anchors(i_body + tittle_i + j_body + tittle_j + curl, system, top="x")
