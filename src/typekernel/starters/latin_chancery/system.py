"""Designer numeric table for latin-chancery (skeleton + pointed pen + flourishes).

Starter so agents reuse pen_dot / flourish / stroke_fragment instead of reinventing.
Construction is skeleton + pen — no heal/blend/seal.
"""

from __future__ import annotations

from typekernel.project import Master
from typekernel.system import Brief, Intent, Overshoot, System, Zones

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
        "endash_width": 400.0,
        "emdash_width": 800.0,
        "slash_width": 280.0,
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
BRIEF = Brief(
    prose=(
        "Chancery italic: broad nib at ~38°, high calligraphic contrast, normal "
        "counters, Regular weight, 0.22 lean. Construction is skeleton + pen; "
        "no heal/blend/seal."
    ),
    intent=Intent(
        contrast="high",
        slant="italic",
        openness="normal",
        weight="regular",
        pen_angle_deg=38.0,
    ),
)
INTENT = BRIEF.intent  # alias for agents / EXTRA tooling


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

# Optical stem kinds for tk audit. Kernel default is named-nodes-only;
# this map is the project opt-in (replaces removed letter tables).
# Empty tuple = no optical probe. Diagonal letters stay quiet here
# (previously auto-info); declare ("diagonal",) to opt into warnings.
AUDIT_STEMS = {
    "A": (),
    "a": (),
    "B": ('vertical',),
    "b": ('vertical',),
    "backslash": (),
    "bracketleft": (),
    "bracketright": (),
    "C": (),
    "c": (),
    "colon": (),
    "comma": (),
    "D": ('vertical',),
    "d": ('vertical',),
    "E": ('vertical',),
    "e": (),
    "eight": (),
    "emdash": (),
    "endash": (),
    "exclam": (),
    "F": ('vertical',),
    "f": ('vertical',),
    "five": (),
    "four": (),
    "G": (),
    "g": ('vertical',),
    "H": ('vertical',),
    "h": ('vertical',),
    "hyphen": (),
    "I": ('vertical',),
    "i": ('vertical',),
    "J": ('vertical',),
    "j": ('vertical',),
    "K": ('vertical',),
    "k": ('vertical',),
    "L": ('vertical',),
    "l": ('vertical',),
    "M": ('vertical',),
    "m": ('vertical',),
    "N": ('vertical',),
    "n": ('vertical',),
    "nine": (),
    "O": (),
    "o": (),
    "one": (),
    "P": ('vertical',),
    "p": ('vertical',),
    "parenleft": (),
    "parenright": (),
    "period": (),
    "Q": (),
    "q": ('vertical',),
    "question": (),
    "quotedbl": (),
    "quotesingle": (),
    "R": ('vertical',),
    "r": ('vertical',),
    "S": (),
    "s": (),
    "semicolon": (),
    "seven": (),
    "six": (),
    "slash": (),
    "T": ('vertical',),
    "t": ('vertical',),
    "three": (),
    "two": (),
    "U": ('vertical',),
    "u": ('vertical',),
    "V": (),
    "v": (),
    "W": (),
    "w": (),
    "X": (),
    "x": (),
    "Y": (),
    "y": (),
    "Z": (),
    "z": (),
    "zero": (),
}
