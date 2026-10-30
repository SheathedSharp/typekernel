"""Project manifest for the latin-sans starter."""

from __future__ import annotations

from pathlib import Path

from composites import COMPOSITES
from expect import EXPECT
from spacing import KERNING, METRICS
from system import (
    INSTANCES,
    WEIGHT_AXIS,
    masters,
    system,
)

from typekernel.axes import MasterSpec
from typekernel.plugins.corners import plain
from typekernel.project import AuditConfig, Charset, FamilyInfo, Project

__all__ = ["PROJECT"]

_CHARSET_DIR = Path(__file__).resolve().parent / "charset"
_CHARSET = Charset.from_text(_CHARSET_DIR / "latin-1.txt") | Charset.from_text(
    _CHARSET_DIR / "latin-ext-a.txt"
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

PROJECT = Project(
    info=FamilyInfo(family="Latin Sans"),
    system=system,
    glyphs="glyphs",
    marks="marks",
    charset=_CHARSET,
    composites=COMPOSITES,
    axes=(WEIGHT_AXIS,),
    masters=tuple(
        MasterSpec(m.name, _MASTER_LOCATIONS.get(m.name, {}), m.system) for m in masters
    ),
    instances=INSTANCES,
    corners={"*": plain()},
    audit=AuditConfig(stems=_AUDIT_STEMS),
    metrics=METRICS,
    kerning=KERNING,
    expect=EXPECT,
    style_name="Regular",
)
