"""Mixed glyph J — anatomy stem + arch_span hook (P3-7)."""

from __future__ import annotations

from elements import WIDTHS, arch_span, zone_anchors

from typekernel.anatomy import stem
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("J", group="uc.mixed")
def glyph_J(system: System):
    st = float(system.stem["uc"])
    cap = float(system.zones.cap)
    width = float(WIDTHS["J"])
    lsb = float(system.tokens.get("lsb_uc", 50.0))
    tension = float(system.tokens.get("shoulder_tension", 0.55))
    x0 = lsb + width - st
    hook_y = st * 1.2
    body = stem(x0, x0 + st, hook_y, cap, name="stem", foot="none")
    tip_x = lsb + st * 0.3
    outer = arch_span(x0 + st, hook_y, tip_x, st * 0.25, -6.0, tension=tension)
    inner = arch_span(
        tip_x + st * 0.75, st * 0.95, x0, hook_y, st * 1.4, tension=tension
    )
    curl = (
        Writer()
        .start((x0, hook_y))
        .corner("hook.entry")
        .line((x0 + st, hook_y))
        .corner("hook.exit")
        .fragment(outer)
        .corner("hook.apex")
        .line((tip_x + st * 0.75, st * 0.95))
        .corner("hook.stress")
        .fragment(inner)
        .close()
        .build()
    )
    return zone_anchors(body + curl, system, top='cap')
