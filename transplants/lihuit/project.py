"""Project manifest for the LihuiT transplant example."""

from __future__ import annotations

from pathlib import Path

from expect import EXPECT
from spacing import KERNING, METRICS
from system import (
    AUDIT_STEMS,
    FAMILY_NAME,
    INSTANCES,
    MASTER_LOCATIONS,
    STYLE_NAME,
    WEIGHT_AXIS,
    masters,
    system,
)

from typekernel.axes import MasterSpec
from typekernel.plugins.corners import plain
from typekernel.project import AuditConfig, Charset, FamilyInfo, Project

__all__ = ["PROJECT"]

_CHARSET_DIR = Path(__file__).resolve().parent / "charset"
# Scope: a–z + 0–9 only for the Hausdorff comparison. Full Latin-1 stays in charset/ for later.
_CHARSET = Charset.from_text(_CHARSET_DIR / "ascii.txt")

PROJECT = Project(
    info=FamilyInfo(family="LihuiT Transplant"),
    system=system,
    glyphs="glyphs",
    marks=None,
    charset=_CHARSET,
    composites=(),  # No composites until anchors are restored.
    axes=(WEIGHT_AXIS,),
    masters=tuple(
        MasterSpec(m.name, MASTER_LOCATIONS.get(m.name, {}), m.system) for m in masters
    ),
    instances=INSTANCES,
    corners={"*": plain()},
    audit=AuditConfig(stems=AUDIT_STEMS),
    metrics=METRICS,
    kerning=KERNING,
    expect=EXPECT,
    style_name=STYLE_NAME,
)
