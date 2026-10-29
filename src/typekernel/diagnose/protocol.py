"""Diagnose protocol v2 (target §7.1)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from typekernel.draw import Drawing
from typekernel.project import Project, ProjectSession
from typekernel.system import System

__all__ = [
    "Check",
    "CheckContext",
    "Finding",
    "Level",
    "Scope",
    "legacy_finding",
]

Scope = Literal["glyph", "pair", "font", "family"]
Level = Literal["error", "warn", "info"]


@dataclass(frozen=True, slots=True)
class Finding:
    check: str
    level: Level
    glyph: str | None
    master: str | None
    where: str | None
    measured: float | str | None
    expected: float | str | None
    message: str
    hint: str = ""

    @property
    def kind(self) -> str:
        """Alias for ``check`` (plugins.checks Finding compatibility)."""
        return self.check

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "level": self.level,
            "glyph": self.glyph,
            "master": self.master,
            "where": self.where,
            "measured": self.measured,
            "expected": self.expected,
            "message": self.message,
            "hint": self.hint,
        }


def legacy_finding(
    kind: str,
    level: str,
    glyph: str,
    message: str,
    *,
    master: str | None = None,
    where: str | None = None,
    measured: float | str | None = None,
    expected: float | str | None = None,
    hint: str = "",
) -> Finding:
    """Bridge from plugins.checks Finding(kind, level, glyph, message)."""
    lvl: Level = "warn"
    if level in ("error", "warn", "info"):
        lvl = level  # type: ignore[assignment]
    return Finding(
        check=kind,
        level=lvl,
        glyph=glyph,
        master=master,
        where=where,
        measured=measured,
        expected=expected,
        message=message,
        hint=hint,
    )


@dataclass
class CheckContext:
    """Inputs for one check invocation (glyph or font scope)."""

    session: ProjectSession
    project: Project
    system: System
    master: str | None = None
    # Active glyph (glyph-scope checks); None for font/family scope.
    name: str | None = None
    raw: Drawing | None = None
    final: Drawing | None = None
    stem_kinds: Mapping[str, Sequence[str]] = field(default_factory=dict)
    declared_stems: Mapping[str, Sequence[str]] = field(default_factory=dict)
    findings: list[Finding] = field(default_factory=list)

    def add(
        self,
        check: str,
        level: Level,
        message: str,
        *,
        glyph: str | None = None,
        where: str | None = None,
        measured: float | str | None = None,
        expected: float | str | None = None,
        hint: str = "",
    ) -> None:
        self.findings.append(
            Finding(
                check=check,
                level=level,
                glyph=self.name if glyph is None else glyph,
                master=self.master,
                where=where,
                measured=measured,
                expected=expected,
                message=message,
                hint=hint,
            )
        )


class Check(Protocol):
    id: str
    scope: Scope

    def run(self, ctx: CheckContext) -> Iterable[Finding]: ...
