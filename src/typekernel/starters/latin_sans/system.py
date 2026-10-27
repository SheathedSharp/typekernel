"""Designer numeric table for the latin-sans starter (ARCHITECTURE.md §3.2)."""

from __future__ import annotations

from typekernel.system import Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=520, cap=700, asc=740, desc=-200),
    overshoot=Overshoot(round=12, pointed=10),
    stem={"lc": 84, "lc_h": 70, "uc": 92, "uc_h": 76},
    tokens={
        "n_width": 430,
        "o_width": 470,
        "H_width": 620,
        "O_width": 700,
        "shoulder_tension": 0.58,
        "bowl_exponent": 2.15,
        "lsb_lc": 40,
        "rsb_lc": 40,
        "lsb_uc": 50,
        "rsb_uc": 50,
        "h_width": 430,
        "m_width": 700,
        "u_width": 430,
        "r_width": 300,
        "n_advance": 510,
        "h_advance": 510,
        "m_advance": 780,
        "u_advance": 510,
        "r_advance": 360,
        "b_advance": 550,
        "d_advance": 550,
        "p_advance": 550,
        "q_advance": 550,
        "v_width": 460,
        "w_width": 700,
        "x_width": 460,
        "y_width": 460,
        "z_width": 460,
        "k_width": 430,
        "v_advance": 540,
        "w_advance": 780,
        "x_advance": 540,
        "y_advance": 540,
        "z_advance": 540,
        "k_advance": 510,
        "o_advance": 550,
        "H_advance": 720,
        "O_advance": 780,
        "bar_thickness": 80,
        "bar_height": 340,
    },
)

masters = ()

FAMILY_NAME = "Latin Sans"
STYLE_NAME = "Regular"
