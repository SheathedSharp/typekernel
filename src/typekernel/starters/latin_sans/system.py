"""Designer numeric table for the latin-sans starter (ARCHITECTURE.md「核心概念」)."""

from __future__ import annotations

from typekernel.project import Master
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
        "bowl_aperture": 0.42,
        "lsb_lc": 40,
        "rsb_lc": 40,
        "space_stem_mul": 2.5,
        "space_lsb_mul": 0.5,
        "lsb_uc": 50,
        "rsb_uc": 50,
        "bar_thickness": 80,
        "bar_height": 340,
    },
)

def _weight_system(base: System, stem_scale: float) -> System:
    """Scale stem thicknesses; overlap construction stays topology-compatible."""
    stem = {k: max(36.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    return base.tuned(stem=stem)


# Project evaluation masters (Regular is the default ``system``).
masters = (
    Master("Light", _weight_system(system, 0.62)),
    Master("Bold", _weight_system(system, 1.38)),
)

# Designspace locations for ``tk build --variable`` (wght user coords).
MASTER_LOCATIONS: dict[str, dict[str, float]] = {
    "Light": {"wght": 300.0},
    "Regular": {"wght": 400.0},
    "Bold": {"wght": 700.0},
}

FAMILY_NAME = "Latin Sans"
STYLE_NAME = "Regular"

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
