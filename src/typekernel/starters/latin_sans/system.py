"""Designer numeric table for the latin-sans starter (ARCHITECTURE.md「核心概念」)."""

from __future__ import annotations

from typekernel.axes import Axis, Instance
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

def _designed_master(
    base: System,
    *,
    stem_scale: float,
    width_scale: float,
    aperture_delta: float = 0.0,
    tension_delta: float = 0.0,
    bar_scale: float = 1.0,
) -> System:
    """Designed weight master — not stem×factor alone.

    Control widths, bowl aperture, shoulder tension, and bar thickness are
    authored per weight so Light/Bold interpolate cleanly on interpolation checks.
    """
    stem = {k: max(36.0, float(v) * stem_scale) for k, v in dict(base.stem).items()}
    tokens = dict(base.tokens)
    for key in ("n_width", "o_width", "H_width", "O_width"):
        if key in tokens:
            tokens[key] = float(tokens[key]) * width_scale
    if "bowl_aperture" in tokens:
        tokens["bowl_aperture"] = min(
            0.9, max(0.1, float(tokens["bowl_aperture"]) + aperture_delta)
        )
    if "shoulder_tension" in tokens:
        tokens["shoulder_tension"] = min(
            0.9, max(0.35, float(tokens["shoulder_tension"]) + tension_delta)
        )
    if "bar_thickness" in tokens:
        tokens["bar_thickness"] = max(40.0, float(tokens["bar_thickness"]) * bar_scale)
    return base.tuned(stem=stem, tokens=tokens)


# Project evaluation masters (Regular is the default ``system``).
# Light: lighter stems, slightly wider counters, opener aperture, softer join.
# Bold: heavier stems, slightly narrower counters, tighter aperture, firmer join.
masters = (
    Master(
        "Light",
        _designed_master(
            system,
            stem_scale=0.62,
            width_scale=1.04,
            aperture_delta=0.04,
            tension_delta=-0.04,
            bar_scale=0.72,
        ),
    ),
    Master(
        "Bold",
        _designed_master(
            system,
            stem_scale=1.38,
            width_scale=0.96,
            aperture_delta=-0.04,
            tension_delta=0.04,
            bar_scale=1.28,
        ),
    ),
)

# Designspace locations for ``tk build --variable`` (wght user coords).
MASTER_LOCATIONS: dict[str, dict[str, float]] = {
    "Light": {"wght": 300.0},
    "Regular": {"wght": 400.0},
    "Bold": {"wght": 700.0},
}


WEIGHT_AXIS = Axis(
    tag="wght",
    name="Weight",
    minimum=100.0,
    default=400.0,
    maximum=900.0,
    labels={
        100.0: "Thin",
        200.0: "ExtraLight",
        300.0: "Light",
        400.0: "Regular",
        500.0: "Medium",
        600.0: "SemiBold",
        700.0: "Bold",
        800.0: "ExtraBold",
        900.0: "Black",
    },
)

INSTANCES: tuple[Instance, ...] = tuple(
    Instance(label, {"wght": coord})
    for coord, label in sorted(WEIGHT_AXIS.labels.items())
)

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
