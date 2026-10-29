"""n-group glyph m — two n-proportion units side by side."""

from __future__ import annotations

from elements import stroke

from typekernel.project import glyph
from typekernel.system import System


@glyph("m", group="lc.straight")
def m(system: System):
    st = float(system.stem["lc"])
    xh = float(system.zones.x)
    # Each unit matches control-n proportions so expand stays signature-stable.
    unit_w = float(system.tokens["n_width"])
    lsb = float(system.tokens["lsb_lc"])
    gap = st * 0.35

    def unit(x_origin: float):
        x0 = x_origin + st * 0.5
        x1 = x_origin + unit_w - st * 0.5
        left = stroke(system, [(x0, 0.0), (x0, xh)], thickness=st)
        right = stroke(system, [(x1, 0.0), (x1, xh * 0.55)], thickness=st)
        arch = stroke(
            system,
            [
                (x0, xh * 0.55),
                (x0, xh),
                ((x0 + x1) / 2.0, xh + st * 0.15),
                (x1, xh),
                (x1, xh * 0.55),
            ],
            thickness=st,
        )
        return left + arch + right

    return unit(lsb) + unit(lsb + unit_w + gap)
