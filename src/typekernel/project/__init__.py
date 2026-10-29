"""project — manifest, @glyph registry, ProjectSession (ARCHITECTURE.md / target §3)."""

from __future__ import annotations

# MasterSpec lives in axes; re-export for project authors.
from typekernel.axes.spec import MasterSpec
from typekernel.project.errors import GlyphBuildError, MigrationError
from typekernel.project.evaluate import unicodes_for_glyph_name
from typekernel.project.manifest import (
    AuditConfig,
    Charset,
    ComponentRef,
    Composite,
    Expect,
    FamilyInfo,
    Project,
    ProofConfig,
    ReviewPolicy,
)
from typekernel.project.registry import GlyphDraft, GlyphSpec, Master, glyph
from typekernel.project.session import ProjectSession, open_project

__all__ = [
    "AuditConfig",
    "Charset",
    "ComponentRef",
    "Composite",
    "Expect",
    "FamilyInfo",
    "GlyphBuildError",
    "GlyphDraft",
    "GlyphSpec",
    "Master",
    "MasterSpec",
    "MigrationError",
    "Project",
    "ProjectSession",
    "ProofConfig",
    "ReviewPolicy",
    "glyph",
    "open_project",
    "unicodes_for_glyph_name",
]
