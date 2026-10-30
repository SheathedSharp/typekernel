"""Numeric table for the latin-sans italic partner.

Zones and stems match latin-sans Regular; slant + pen tokens author the italic.
"""

from __future__ import annotations

from typekernel.project import Master
from typekernel.system import Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=520, cap=700, asc=740, desc=-200),
    overshoot=Overshoot(round=12, pointed=10),
    stem={"lc": 84, "lc_h": 70, "uc": 92, "uc_h": 76},
    slant=0.16,
    tokens={
        "pen_contrast": 0.70,
        "pen_angle_deg": 12.0,
        "n_width": 470,
        "o_width": 470,
        "H_width": 620,
        "O_width": 700,
        "lsb_lc": 40,
        "lsb_uc": 50,
        "space_stem_mul": 2.5,
        "space_lsb_mul": 0.5,
        "bowl_aperture_deg": 72.0,
    },
)

def _designed_master(base: System, *, stem_scale: float, width_scale: float) -> System:
    stem = {k: max(36.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    tokens = dict(base.tokens)
    for key in ("n_width", "o_width", "H_width", "O_width"):
        if key in tokens:
            tokens[key] = float(tokens[key]) * width_scale
    return base.tuned(stem=stem, tokens=tokens)

masters: tuple[Master, ...] = (
    Master("Light", _designed_master(system, stem_scale=0.62, width_scale=1.04)),
    Master("Bold", _designed_master(system, stem_scale=1.38, width_scale=0.96)),
)

