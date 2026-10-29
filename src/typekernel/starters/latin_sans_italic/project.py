"""Project manifest — latin-sans italic partner (P5-3)."""

from __future__ import annotations

from expect import EXPECT
from spacing import KERNING, METRICS
from system import (
    FAMILY_NAME,
    MASTER_LOCATIONS,
    STYLE_NAME,
    masters,
    system,
)

from typekernel.axes import MasterSpec
from typekernel.project import FamilyInfo, Project

__all__ = ["PROJECT"]

PROJECT = Project(
    info=FamilyInfo(family=FAMILY_NAME),
    system=system,
    glyphs="glyphs",
    masters=tuple(
        MasterSpec(m.name, MASTER_LOCATIONS.get(m.name, {}), m.system) for m in masters
    ),
    metrics=METRICS,
    kerning=KERNING,
    expect=EXPECT,
    style_name=STYLE_NAME,
)
