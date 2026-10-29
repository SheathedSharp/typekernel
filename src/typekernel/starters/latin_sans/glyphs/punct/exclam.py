"""exclam — anatomy stem + dot ."""

from __future__ import annotations

from typekernel.anatomy import dot, stem
from typekernel.project import glyph
from typekernel.system import System


@glyph("exclam", group="punct")
def exclam(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    size = st * 0.95
    lsb = float(system.tokens.get("lsb_lc", 40.0)) * 0.55
    x0 = lsb + (size - st) / 2.0
    body = stem(x0, x0 + st, size * 1.35, xh, name="stem")
    tittle = dot((lsb + size / 2.0, size / 2.0), size, shape="square", name="dot")
    return body + tittle
