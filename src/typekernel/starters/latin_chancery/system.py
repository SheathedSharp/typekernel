"""Designer numeric table for latin-chancery (skeleton + pointed pen + flourishes).

Starter so agents reuse pen_dot / flourish / stroke_fragment instead of reinventing.
Construction is skeleton + pen — no heal/blend/seal.
"""

from __future__ import annotations

from typekernel.project import Master
from typekernel.system import Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=480, cap=680, asc=780, desc=-240),
    overshoot=Overshoot(round=16, pointed=12),
    stem={"lc": 64, "lc_h": 36, "uc": 72, "uc_h": 40},
    slant=0.22,
    tokens={
        "pen_contrast": 0.28,
        "pen_angle_deg": 38.0,
        "n_width": 380.0,
        "o_width": 400.0,
        "H_width": 540.0,
        "O_width": 580.0,
        "lsb_lc": 32.0,
        "lsb_uc": 40.0,
        "arch_rise": 0.14,
        "flourish_depth": 90.0,
        "dot_radius": 28.0,
        "space_stem_mul": 2.5,
        "space_lsb_mul": 0.5,
    },
)

# Typed intent (checked by ``tk audit``). Prose twin: brief.md.
# Mapping tables: typekernel.system.intent — not an aesthetics score.

def _weight_system(base: System, stem_scale: float) -> System:
    stem = {k: max(28.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    return base.tuned(stem=stem)

# Masters kept for Regular-first builds; enable VF only when signatures stay stable.
masters = (
    Master(name="Light", system=_weight_system(system, 0.62)),
    Master(name="Bold", system=_weight_system(system, 1.28)),
)

