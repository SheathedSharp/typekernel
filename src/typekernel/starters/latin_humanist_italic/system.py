"""Designer numeric table for latin-humanist-italic (ARCHITECTURE.md「构造插件」).

Construction is skeleton + broad nib — not contour Writer outlines.

Light/Bold masters scale ``stem`` only; ``expand_skeleton`` promotes lines to
cubics so ``Drawing.signature()`` stays thickness-stable for VF.
"""

from __future__ import annotations

from typekernel.project import Master
from typekernel.system import Brief, Intent, Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
    overshoot=Overshoot(round=14, pointed=10),
    stem={"lc": 72, "lc_h": 58, "uc": 80, "uc_h": 64},
    # Italic lean: Δx = slant * Δy (System field — not a token).
    slant=0.18,
    tokens={
        "pen_contrast": 0.52,
        "pen_angle_deg": 28.0,
        "n_width": 400.0,
        "m_width": 640.0,
        "o_width": 420.0,
        "H_width": 560.0,
        "O_width": 620.0,
        "lsb_lc": 36.0,
        "lsb_uc": 44.0,
        # space advance = stem[lc]*space_stem_mul + n_lsb*space_lsb_mul
        "space_stem_mul": 2.5,
        "space_lsb_mul": 0.5,
        "arch_rise": 0.12,
        # Remaining ASCII widths (skeleton extents before spacing pack).
        "f_width": 260.0,
        "t_width": 280.0,
        "r_width": 280.0,
        "k_width": 400.0,
        "v_width": 400.0,
        "w_width": 620.0,
        "x_width": 400.0,
        "y_width": 400.0,
        "z_width": 400.0,
        "s_width": 360.0,
        "g_width": 420.0,
        "L_width": 480.0,
        "E_width": 500.0,
        "F_width": 460.0,
        "T_width": 560.0,
        "N_width": 600.0,
        "M_width": 760.0,
        "U_width": 600.0,
        "A_width": 620.0,
        "V_width": 620.0,
        "W_width": 900.0,
        "X_width": 600.0,
        "Y_width": 600.0,
        "Z_width": 560.0,
        "K_width": 580.0,
        "G_width": 640.0,
        "D_width": 600.0,
        "B_width": 560.0,
        "P_width": 520.0,
        "R_width": 580.0,
        "J_width": 460.0,
        "S_width": 540.0,
        "fig_width": 460.0,
        "question_width": 300.0,
        "hyphen_width": 200.0,
        "endash_width": 400.0,
        "emdash_width": 800.0,
        "slash_width": 280.0,
    },
)


# Typed intent (checked by ``tk audit``). Prose twin: brief.md.
# Mapping tables: typekernel.system.intent — not an aesthetics score.
BRIEF = Brief(
    prose=(
        "Humanist true italic: broad nib at ~28°, medium calligraphic contrast, "
        "normal counters, Regular weight. Construction is skeleton + pen; "
        "no heal/blend/seal."
    ),
    intent=Intent(
        contrast="medium",
        slant="italic",
        openness="normal",
        weight="regular",
        pen_angle_deg=28.0,
    ),
)
INTENT = BRIEF.intent  # alias for agents / EXTRA tooling


def _weight_system(base: System, stem_scale: float) -> System:
    """Scale stem thicknesses; skeleton topology must stay master-compatible."""
    stem = {k: max(36.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    return base.tuned(stem=stem)


# Project evaluation masters (Regular is the default ``system``).
masters: tuple[Master, ...] = (
    Master("Light", _weight_system(system, 0.62)),
    Master("Bold", _weight_system(system, 1.38)),
)

# Designspace locations for ``tk build --variable`` (wght user coords).
MASTER_LOCATIONS: dict[str, dict[str, float]] = {
    "Light": {"wght": 300.0},
    "Regular": {"wght": 400.0},
    "Bold": {"wght": 700.0},
}

FAMILY_NAME = "Latin Humanist Italic"
STYLE_NAME = "Italic"
