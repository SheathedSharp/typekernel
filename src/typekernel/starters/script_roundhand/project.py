"""Project manifest for script-roundhand."""

from __future__ import annotations

from expect import EXPECT
from spacing import KERNING, METRICS
from system import system

from typekernel.project import AuditConfig, FamilyInfo, Project
from typekernel.system import Brief, Intent

__all__ = ["PROJECT"]

BRIEF = Brief(
    prose=(
        "Pointed roundhand: thin upstrokes / thick downstrokes, italic lean, "
        "Stroke.through + expand_pointed. Intent.tool=pointed, genre=roundhand."
    ),
    intent=Intent(
        contrast="high",
        slant="italic",
        openness="normal",
        weight="regular",
        pen_angle_deg=28.0,
        tool="pointed",
        connection="full",
        genre="roundhand",
    ),
)

_AUDIT_STEMS = {
    "a": (),
    "c": (),
    "e": (),
    "f": (),
    "i": (),
    "l": (),
    "n": (),
    "o": (),
    "r": (),
    "u": (),
    "v": (),
    "y": (),
    "z": (),
}

PROJECT = Project(
    info=FamilyInfo(family="ScriptRoundhand", italic=True),
    system=system,
    glyphs="glyphs",
    masters=(),
    audit=AuditConfig(stems=_AUDIT_STEMS),
    brief=BRIEF,
    metrics=METRICS,
    kerning=KERNING,
    expect=EXPECT,
    style_name="Italic",
)
