"""Project manifest — latin-sans italic partner."""

from __future__ import annotations

from expect import EXPECT
from spacing import KERNING, METRICS
from system import (
    masters,
    system,
)

from typekernel.axes import MasterSpec
from typekernel.project import FamilyInfo, Project
from typekernel.system import Brief, Intent

__all__ = ["PROJECT"]

BRIEF = Brief(
    prose=(
        "Latin Sans true italic partner: same proportions as latin-sans, "
        "mild italic slant, low-contrast pen for a sans-adjacent italic."
    ),
    intent=Intent(
        contrast="low",
        slant="italic",
        openness="normal",
        weight="regular",
        pen_angle_deg=12.0,
    ),
)

_MASTER_LOCATIONS: dict[str, dict[str, float]] = {
    "Light": {"wght": 300.0},
    "Regular": {"wght": 400.0},
    "Bold": {"wght": 700.0},
}

PROJECT = Project(
    info=FamilyInfo(family="Latin Sans", italic=True),
    system=system,
    glyphs="glyphs",
    masters=tuple(
        MasterSpec(m.name, _MASTER_LOCATIONS.get(m.name, {}), m.system) for m in masters
    ),
    metrics=METRICS,
    kerning=KERNING,
    expect=EXPECT,
    brief=BRIEF,
    style_name="Italic",
)
