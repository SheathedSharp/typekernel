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
        "e_width": 400.0,
        "h_width": 380.0,
        "m_width": 620.0,
        "k_width": 360.0,
        "r_width": 240.0,
        "s_width": 340.0,
        "v_width": 360.0,
        "w_width": 560.0,
        "x_width": 360.0,
        "y_width": 360.0,
        "z_width": 340.0,
        "A_width": 560.0,
        "B_width": 520.0,
        "D_width": 560.0,
        "E_width": 480.0,
        "F_width": 460.0,
        "J_width": 360.0,
        "K_width": 520.0,
        "L_width": 460.0,
        "M_width": 700.0,
        "N_width": 560.0,
        "P_width": 500.0,
        "R_width": 540.0,
        "S_width": 480.0,
        "T_width": 520.0,
        "U_width": 560.0,
        "V_width": 560.0,
        "W_width": 780.0,
        "X_width": 540.0,
        "Y_width": 540.0,
        "Z_width": 520.0,
        "fig_width": 420.0,
        "hyphen_width": 220.0,
        "lsb_lc": 32.0,
        "lsb_uc": 40.0,
        "arch_rise": 0.14,
        "flourish_depth": 90.0,
        "dot_radius": 28.0,
        "space_stem_mul": 2.5,
        "space_lsb_mul": 0.5,
        # Multi-band italic packing (fraction of x-height for silhouette samples).
        "italic_pack_ys": (0.28, 0.5, 0.72),
    },
)


def _weight_system(base: System, stem_scale: float) -> System:
    stem = {k: max(28.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    return base.tuned(stem=stem)


# Masters kept for Regular-first builds; enable VF only when signatures stay stable.
masters = (
    Master(name="Light", system=_weight_system(system, 0.62)),
    Master(name="Bold", system=_weight_system(system, 1.28)),
)

FAMILY_NAME = "LatinChancery"
STYLE_NAME = "Italic"

# Oriented-stem audit: only glyphs with intentional vertical ink.
AUDIT_STEMS = {
    "n": ("vertical",),
    "h": ("vertical",),
    "m": ("vertical",),
    "u": ("vertical",),
    "i": ("vertical",),
    "l": ("vertical",),
    "b": ("vertical",),
    "d": ("vertical",),
    "p": ("vertical",),
    "q": ("vertical",),
    "H": ("vertical",),
    "I": ("vertical",),
    "E": ("vertical",),
    "F": ("vertical",),
    "L": ("vertical",),
    "o": (),
    "O": (),
    "e": (),
    "c": (),
    "s": (),
    "a": (),
    "v": (),
    "w": (),
    "x": (),
    "y": (),
    "z": (),
    "A": (),
    "V": (),
    "W": (),
    "X": (),
    "Y": (),
    "Z": (),
    "zero": (),
    "eight": (),
}
