"""Designer numeric table for latin-humanist-italic (ARCHITECTURE.md「构造插件」).

Construction is skeleton + broad nib — not contour Writer outlines.

Light/Bold masters scale ``stem`` only; ``expand_skeleton`` promotes lines to
cubics so ``Drawing.signature()`` stays thickness-stable for VF.
"""

from __future__ import annotations

from typekernel.project import Master
from typekernel.system import Overshoot, System, Zones

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
    },
)

# Typed intent (checked by ``tk audit``). Prose twin: brief.md.
# Mapping tables: typekernel.system.intent — not an aesthetics score.

def _designed_master(
    base: System,
    *,
    stem_scale: float,
    width_scale: float,
    aperture_delta: float = 0.0,
) -> System:
    """Designed weight master — stem + control widths (designed-master style)."""
    stem = {k: max(36.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    tokens = dict(base.tokens)
    for key in ("n_width", "o_width", "H_width", "O_width"):
        if key in tokens:
            tokens[key] = float(tokens[key]) * width_scale
    # Keep pen angle stable; slight contrast nudge with weight.
    contrast = float(tokens.get("pen_contrast", 0.52))
    tokens["pen_contrast"] = max(0.35, min(0.75, contrast + (stem_scale - 1.0) * 0.04))
    if "bowl_aperture" in tokens:
        tokens["bowl_aperture"] = float(tokens["bowl_aperture"]) + aperture_delta
    return base.tuned(stem=stem, tokens=tokens)

# Project evaluation masters (Regular is the default ``system``).
masters: tuple[Master, ...] = (
    Master(
        "Light",
        _designed_master(system, stem_scale=0.62, width_scale=1.04, aperture_delta=0.03),
    ),
    Master(
        "Bold",
        _designed_master(system, stem_scale=1.38, width_scale=0.96, aperture_delta=-0.03),
    ),
)

# Designspace locations for ``tk build --variable`` (wght user coords).

