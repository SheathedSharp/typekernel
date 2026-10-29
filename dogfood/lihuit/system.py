"""System for LihuiT dogfood — zones/stems aligned to published Regular (P6-3)."""

from __future__ import annotations

from typekernel.axes import Axis, Instance
from typekernel.project import Master
from typekernel.system import Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=552, cap=730, asc=748, desc=-210),
    overshoot=Overshoot(round=0, pointed=0),
    stem={"lc": 66, "lc_h": 56, "uc": 66, "uc_h": 56},
    tokens={
        "n_width": 644,
        "o_width": 644,
        "H_width": 738,
        "O_width": 700,
        "lsb_lc": 57,
        "rsb_lc": 57,
        "lsb_uc": 57,
        "rsb_uc": 57,
        "space_stem_mul": 2.5,
        "space_lsb_mul": 0.5,
        "shoulder_tension": 0.58,
        "bowl_exponent": 2.15,
        "bowl_aperture": 0.42,
        "bar_thickness": 66,
        "bar_height": 340,
    },
    slant=0.0,
)

# Single Regular master: Bold static outlines are not VF-compatible with Regular
# (different point counts). Bold Hausdorff uses ref_outlines weight="Bold".
masters = (
    Master("Regular", system),
)

MASTER_LOCATIONS: dict[str, dict[str, float]] = {
    "Regular": {"wght": 400.0},
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

INSTANCES: tuple[Instance, ...] = (Instance("Regular", {"wght": 400.0}),)

FAMILY_NAME = "LihuiT Dogfood"
STYLE_NAME = "Regular"

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

