"""Numeric table for latin-sans italic partner (P5-3 / DQ5).

Zones and stems match latin-sans Regular; slant + pen tokens author the italic.
"""

from __future__ import annotations

from typekernel.project import Master
from typekernel.system import Brief, Intent, Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=520, cap=700, asc=740, desc=-200),
    overshoot=Overshoot(round=12, pointed=10),
    stem={"lc": 84, "lc_h": 70, "uc": 92, "uc_h": 76},
    slant=0.16,
    tokens={
        "pen_contrast": 0.62,
        "pen_angle_deg": 12.0,
        "n_width": 430,
        "m_width": 680,
        "o_width": 470,
        "r_width": 300,
        "l_width": 220,
        "v_width": 420,
        "w_width": 640,
        "x_width": 420,
        "y_width": 420,
        "z_width": 420,
        "k_width": 420,
        "s_width": 380,
        "A_width": 640,
        "V_width": 640,
        "N_width": 620,
        "M_width": 780,
        "K_width": 600,
        "H_width": 620,
        "O_width": 700,
        "I_width": 220,
        "L_width": 500,
        "T_width": 560,
        "E_width": 520,
        "F_width": 480,
        "lsb_lc": 40,
        "lsb_uc": 50,
        "space_stem_mul": 2.5,
        "space_lsb_mul": 0.5,
        "bowl_aperture_deg": 72.0,
    },
)

BRIEF = Brief(
    prose=(
        "Latin Sans true italic partner: same proportions as latin-sans, "
        "mild italic slant, low-contrast pen for a sans-adjacent italic."
    ),
    intent=Intent(
        contrast="low",
        slant="italic",
        openness="normal",
        weight="regular",
        pen_angle_deg=12.0,
    ),
)
INTENT = BRIEF.intent


def _designed_master(base: System, *, stem_scale: float, width_scale: float) -> System:
    stem = {k: max(36.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    tokens = dict(base.tokens)
    for key in ("n_width", "m_width", "o_width", "H_width", "O_width", "r_width", "L_width", "T_width", "E_width", "F_width", "v_width", "w_width", "x_width", "y_width", "z_width", "k_width", "A_width", "V_width", "N_width", "M_width", "K_width"):
        if key in tokens:
            tokens[key] = float(tokens[key]) * width_scale
    return base.tuned(stem=stem, tokens=tokens)


masters: tuple[Master, ...] = (
    Master("Light", _designed_master(system, stem_scale=0.62, width_scale=1.04)),
    Master("Bold", _designed_master(system, stem_scale=1.38, width_scale=0.96)),
)

MASTER_LOCATIONS: dict[str, dict[str, float]] = {
    "Light": {"wght": 300.0},
    "Regular": {"wght": 400.0},
    "Bold": {"wght": 700.0},
}

FAMILY_NAME = "Latin Sans"
STYLE_NAME = "Italic"
