"""question — anatomy bars/stem/dot ."""

from __future__ import annotations

from elements import WIDTHS

from typekernel.anatomy import crossbar, dot, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("question", group="punct")
def question(system: System):
    st = float(system.stem["lc"])
    thin = float(system.stem.get("lc_h", st * 0.85))
    xh = float(system.zones.x)
    size = st * 0.95
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.4
    width = float(WIDTHS.get("question", 320))
    top = crossbar(
        lsb + width * 0.15,
        lsb + width,
        xh - thin / 2.0,
        thick=thin,
        name="bar",
        ends="none",
    )
    body = stem(
        lsb + width - st * 1.1,
        lsb + width - st * 0.1,
        xh * 0.42,
        xh - thin * 0.5,
        name="stem",
        top="none",
    )
    stub = stem(
        lsb + width * 0.42,
        lsb + width * 0.42 + st,
        xh * 0.38,
        xh * 0.55,
        name="spur",
    )
    tittle = dot(
        (lsb + width * 0.42 + size / 2.0, size / 2.0),
        size,
        shape="square",
        name="dot",
    )
    return top + body + stub + tittle
