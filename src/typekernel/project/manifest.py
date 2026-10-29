"""Project manifest types (target-architecture §3.2)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from typekernel.axes.spec import Axis, Instance, MasterSpec
from typekernel.draw import CornerFiller, EndFiller
from typekernel.features import Features
from typekernel.metrics import Kerning, Metrics
from typekernel.system import Brief, System

__all__ = [
    "AuditConfig",
    "Charset",
    "ComponentRef",
    "Composite",
    "Expect",
    "FamilyInfo",
    "Project",
    "ProofConfig",
    "ReviewPolicy",
]


@dataclass(frozen=True, slots=True)
class FamilyInfo:
    family: str
    designer: str = ""
    version: str = "0.001"
    vendor: str = ""
    license: str = ""
    license_url: str = ""
    copyright: str = ""


@dataclass(frozen=True, slots=True)
class Charset:
    codepoints: frozenset[int]
    extra_names: frozenset[str] = frozenset()

    @classmethod
    def from_text(cls, path: str | Path) -> Charset:
        """Parse a charset file: one character, U+XXXX, or glyph name per line."""
        cps: set[int] = set()
        names: set[str] = set()
        text = Path(path).read_text(encoding="utf-8")
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith(("U+", "u+")):
                cps.add(int(line[2:], 16))  # noqa: FURB166 - U+XXXX form, not 0x
            elif len(line) == 1:
                cps.add(ord(line))
            else:
                names.add(line)
        return cls(frozenset(cps), frozenset(names))

    def __or__(self, other: Charset) -> Charset:
        return Charset(
            self.codepoints | other.codepoints,
            self.extra_names | other.extra_names,
        )


@dataclass(frozen=True, slots=True)
class Expect:
    """Per-glyph topology / reach expectations (diagnose §7.3)."""

    counters: int | None = None
    islands: int | None = None
    apertures: int | None = None
    reach: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AuditConfig:
    """Project audit policy. ``stems`` replaces module-level ``AUDIT_STEMS``."""

    stems: Mapping[str, Sequence[str]] = field(default_factory=dict)
    extra_checks: tuple[Callable[..., Any], ...] = ()

    def __post_init__(self) -> None:
        frozen = {str(k): tuple(v) for k, v in dict(self.stems).items()}
        object.__setattr__(self, "stems", MappingProxyType(frozen))


@dataclass(frozen=True, slots=True)
class ProofConfig:
    """Project proof strings / sets (perceive §6). Placeholder until P2."""

    control: str = ""
    spacing: tuple[str, ...] = ()
    kern: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ReviewPolicy:
    """Review / task-board policy (review §8). Placeholder until P2."""

    groups: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "groups",
            MappingProxyType({str(k): tuple(v) for k, v in dict(self.groups).items()}),
        )


@dataclass(frozen=True, slots=True)
class ComponentRef:
    """Reference to another glyph placed with an affine transform."""

    base: str
    transform: tuple[float, float, float, float, float, float] = (
        1.0,
        0.0,
        0.0,
        1.0,
        0.0,
        0.0,
    )


@dataclass(frozen=True, slots=True)
class Composite:
    """Composite glyph declaration (base + marks at anchors)."""

    base: str
    marks: Sequence[str] = ()
    unicodes: Sequence[int] | None = None


@dataclass(frozen=True, slots=True)
class Project:
    """Declarative project manifest (target-architecture §3.2).

    Evaluation / build / diagnose go through :class:`ProjectSession`.
    """

    info: FamilyInfo
    system: System
    glyphs: str | Path = "glyphs"
    marks: str | Path | None = "marks"
    axes: Sequence[Axis] = ()
    masters: Sequence[MasterSpec] = ()
    instances: Sequence[Instance] = ()
    charset: Charset | None = None
    composites: Mapping[str, Composite] = field(default_factory=dict)
    corners: Mapping[str, CornerFiller] | None = None
    ends: Mapping[str, EndFiller] | None = None
    metrics: Metrics | None = None
    kerning: Kerning | None = None
    features: Features = field(default_factory=Features)
    expect: Mapping[str, Expect] = field(default_factory=dict)
    audit: AuditConfig = field(default_factory=AuditConfig)
    proofs: ProofConfig = field(default_factory=ProofConfig)
    review: ReviewPolicy = field(default_factory=ReviewPolicy)
    brief: Brief | None = None
    style_name: str = "Regular"

    def __post_init__(self) -> None:
        object.__setattr__(self, "axes", tuple(self.axes))
        object.__setattr__(self, "masters", tuple(self.masters))
        object.__setattr__(self, "instances", tuple(self.instances))
        object.__setattr__(
            self,
            "composites",
            MappingProxyType(dict(self.composites)),
        )
        if self.corners is not None:
            object.__setattr__(self, "corners", MappingProxyType(dict(self.corners)))
        if self.ends is not None:
            object.__setattr__(self, "ends", MappingProxyType(dict(self.ends)))
        object.__setattr__(self, "expect", MappingProxyType(dict(self.expect)))
