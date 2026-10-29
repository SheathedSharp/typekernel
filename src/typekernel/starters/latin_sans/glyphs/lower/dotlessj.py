"""dotlessj — j without tittle (P4-2 composite base)."""

from __future__ import annotations

from elements import WIDTHS, arch_span, zone_anchors

from typekernel.anatomy import stem
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("dotlessj", unicodes=(), group="lc.straight")
def dotlessj(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    desc = float(system.zones.desc)
    width = float(WIDTHS["j"])
    lsb = float(system.tokens.get("lsb_lc", 40.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    x0 = lsb + (width - st) / 2.0
    hook_y = desc + st * 1.1
    body = stem(x0, x0 + st, hook_y, xh, name="stem")
    x_l = x0 + st - width * 0.85
    outer = arch_span(x0 + st, hook_y, x_l, desc + st * 0.2, desc - 4.0, tension=tension)
    inner = arch_span(
        x_l + st * 0.7,
        desc + st * 0.85,
        x0,
        hook_y,
        desc + st * 1.35,
        tension=tension,
    )
    curl = (
        Writer()
        .start((x0, hook_y))
        .corner("hook.entry")
        .line((x0 + st, hook_y))
        .corner("hook.exit")
        .fragment(outer)
        .corner("hook.apex")
        .line((x_l + st * 0.7, desc + st * 0.85))
        .corner("hook.stress")
        .fragment(inner)
        .close()
        .build()
    )
    return zone_anchors(body + curl, system, top="x")
