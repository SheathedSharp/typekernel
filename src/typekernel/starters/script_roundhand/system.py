"""Designer numeric table for script-roundhand (pointed pen)."""

from __future__ import annotations

from typekernel.project import Master
from typekernel.system import Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=480, cap=700, asc=780, desc=-260),
    overshoot=Overshoot(round=10, pointed=14),
    stem={"lc": 72, "lc_h": 16, "uc": 80, "uc_h": 20},
    slant=0.20,
    tokens={
        "pen_contrast": 1.0,
        "pen_angle_deg": 28.0,
        "n_width": 420.0,
        "o_width": 440.0,
        "lsb_lc": 28.0,
        "space_stem_mul": 2.4,
        "space_lsb_mul": 0.5,
    },
)


def _weight_system(base: System, stem_scale: float) -> System:
    stem = {k: max(12.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    return base.tuned(stem=stem)


masters = (
    Master(name="Light", system=_weight_system(system, 0.7)),
    Master(name="Bold", system=_weight_system(system, 1.25)),
)
