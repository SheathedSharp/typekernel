"""Check plugin protocol for ``tk audit`` / project EXTRA_CHECKS."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Protocol

from typekernel.draw import Drawing
from typekernel.project import Project
from typekernel.system import System

__all__ = [
    "CheckContext",
    "CheckFn",
    "Finding",
    "raw_drawing",
]


@dataclass
class Finding:
    kind: str  # stem | zone | direction | compat | overlap | custom
    level: str  # error | warn | info
    glyph: str
    message: str


@dataclass
class CheckContext:
    """Per-glyph inputs for a check plugin."""

    name: str
    raw: Drawing
    final: Drawing
    system: System
    project: Project
    stem_kinds: Mapping[str, Sequence[str]]
    findings: list[Finding] = field(default_factory=list)


class CheckFn(Protocol):
    def __call__(self, ctx: CheckContext) -> None: ...


def raw_drawing(project: Project, name: str, *, master: str | None = None) -> Drawing:
    """Pre-slot drawing so named corner nodes remain measurable."""
    spec = project.specs()[name]
    system = project.system
    build = spec.build
    if master is not None:
        by = {m.name: m for m in project.masters}
        if master in by:
            system = by[master].system
        if master in spec.masters:
            build = spec.masters[master]
    return build(system)
