"""Designer numeric table for latin-humanist-italic (ARCHITECTURE.md M6).

Construction is skeleton + broad nib — not contour Writer outlines.
"""

from __future__ import annotations

from typekernel.system import Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
    overshoot=Overshoot(round=14, pointed=10),
    stem={"lc": 72, "lc_h": 58, "uc": 80, "uc_h": 64},
    tokens={
        # Italic lean: Δx = slant * Δy (design units per unit rise).
        "slant": 0.18,
        "pen_contrast": 0.52,
        "pen_angle_deg": 28.0,
        "n_width": 400.0,
        "m_width": 640.0,
        "o_width": 420.0,
        "H_width": 560.0,
        "O_width": 620.0,
        "lsb_lc": 36.0,
        "lsb_uc": 44.0,
        "arch_rise": 0.12,
    },
)

masters = ()

FAMILY_NAME = "Latin Humanist Italic"
STYLE_NAME = "Italic"
