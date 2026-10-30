"""Project manifest for the latin-humanist-italic starter."""

from __future__ import annotations

from expect import EXPECT
from spacing import KERNING, METRICS
from system import (
    masters,
    system,
)

from typekernel.axes import MasterSpec
from typekernel.project import AuditConfig, FamilyInfo, Project
from typekernel.system import Brief, Intent

__all__ = ["PROJECT"]

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

_MASTER_LOCATIONS: dict[str, dict[str, float]] = {
    "Light": {"wght": 300.0},
    "Regular": {"wght": 400.0},
    "Bold": {"wght": 700.0},
}

_AUDIT_STEMS = {
    "A": (),
    "a": (),
    "B": ('vertical',),
    "b": (),
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
    "q": (),
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

PROJECT = Project(
    info=FamilyInfo(family="Latin Humanist Italic", italic=True),
    system=system,
    glyphs="glyphs",
    masters=tuple(
        MasterSpec(m.name, _MASTER_LOCATIONS.get(m.name, {}), m.system) for m in masters
    ),
    audit=AuditConfig(stems=_AUDIT_STEMS),
    brief=BRIEF,
    metrics=METRICS,
    kerning=KERNING,
    expect=EXPECT,
    style_name="Italic",
)
