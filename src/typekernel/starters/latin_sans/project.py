"""Project manifest for the latin-sans starter."""

from __future__ import annotations

from spacing import KERNING, METRICS
from system import (
    AUDIT_STEMS,
    FAMILY_NAME,
    MASTER_LOCATIONS,
    STYLE_NAME,
    masters,
    system,
)

from typekernel.axes import MasterSpec
from typekernel.plugins.corners import plain
from typekernel.project import AuditConfig, FamilyInfo, Project

__all__ = ["PROJECT"]

PROJECT = Project(
    info=FamilyInfo(family=FAMILY_NAME),
    system=system,
    glyphs="glyphs",
    masters=tuple(
        MasterSpec(m.name, MASTER_LOCATIONS.get(m.name, {}), m.system) for m in masters
    ),
    corners={"*": plain()},
    audit=AuditConfig(stems=AUDIT_STEMS),
    metrics=METRICS,
    kerning=KERNING,
    style_name=STYLE_NAME,
)
