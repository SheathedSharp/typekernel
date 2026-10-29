"""Project manifest for the latin-chancery starter."""

from __future__ import annotations

from system import (
    AUDIT_STEMS,
    BRIEF,
    FAMILY_NAME,
    STYLE_NAME,
    masters,
    system,
)

from typekernel.axes import MasterSpec
from typekernel.project import AuditConfig, FamilyInfo, Project

__all__ = ["PROJECT"]

# Chancery has no MASTER_LOCATIONS yet; empty design locations until VF is enabled.
PROJECT = Project(
    info=FamilyInfo(family=FAMILY_NAME),
    system=system,
    glyphs="glyphs",
    masters=tuple(MasterSpec(m.name, {}, m.system) for m in masters),
    audit=AuditConfig(stems=AUDIT_STEMS),
    brief=BRIEF,
    style_name=STYLE_NAME,
)
