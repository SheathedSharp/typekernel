"""Load a user project directory via :class:`~typekernel.project.ProjectSession`."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from typekernel.font.font import Font
from typekernel.metrics.applying import apply_kerning, apply_metrics
from typekernel.project import Project, ProjectSession, open_project
from typekernel.system import System

__all__ = [
    "apply_project_spacing",
    "apply_project_spacing_with_system",
    "build_font_from_project",
    "build_font_from_session",
    "load_project",
    "open_project",
]


def load_project(root: str | Path) -> Project:
    """Open ``root`` briefly and return its frozen :class:`~typekernel.project.Project`.

    Prefer keeping a :class:`~typekernel.project.ProjectSession` open when
    evaluating glyphs. This helper only returns the manifest declaration.
    """
    with open_project(root) as session:
        return cast(Project, session.project)


def build_font_from_session(
    session: ProjectSession,
    *,
    family_name: str | None = None,
    style_name: str | None = None,
    apply_spacing: bool = True,
    master: str | None = None,
) -> Font:
    """Assemble a Font from an open session (isolated imports already active)."""
    project = session.project
    system = project.system
    if master is not None:
        by_name = {m.name: m for m in project.masters}
        if master not in by_name:
            raise KeyError(f"unknown master {master!r}")
        system = by_name[master].system
    family = family_name or project.info.family
    style = style_name or project.style_name
    font = Font.from_system(system, family, style)
    for name in session.specs():
        font.add_glyph(session.glyph(name, master=master), replace=True)
    if apply_spacing:
        apply_project_spacing(font, project, session.root)
    return font


def apply_project_spacing(font: Font, project: Project, project_root: Path) -> None:
    """Apply ``Project.metrics`` / ``kerning``, or legacy ``spacing.apply_spacing``."""
    apply_project_spacing_with_system(
        font, project.system, project_root, project=project
    )


def build_font_from_project(
    project: Project,
    *,
    family_name: str | None = None,
    style_name: str | None = None,
    project_root: str | Path | None = None,
    apply_spacing: bool = True,
    master: str | None = None,
) -> Font:
    """Assemble a Font; ``project_root`` is required for on-disk glyph discovery."""
    if project_root is None:
        raise ValueError(
            "build_font_from_project requires project_root=... "
            "(open_project / ProjectSession owns glyph discovery)"
        )
    root = Path(project_root).resolve()
    with open_project(root) as session:
        return build_font_from_session(
            session,
            family_name=family_name or project.info.family,
            style_name=style_name or project.style_name,
            apply_spacing=apply_spacing,
            master=master,
        )


def apply_project_spacing_with_system(
    font: Font,
    system: System,
    project_root: Path,
    *,
    project: Project | None = None,
) -> None:
    """Apply metrics from ``project`` when set; else legacy ``spacing.apply_spacing``."""
    if project is not None and project.metrics is not None:
        apply_metrics(font, project.metrics, system)
        if project.kerning is not None:
            apply_kerning(font, project.kerning)
        return

    spacing_py = Path(project_root) / "spacing.py"
    if not spacing_py.is_file():
        return
    root_resolved = Path(project_root).resolve()
    apply_fn: Callable[..., Any] | None = None
    bare = sys.modules.get("spacing")
    if bare is not None:
        bare_file = getattr(bare, "__file__", "") or ""
        if bare_file and Path(bare_file).resolve().parent == root_resolved:
            candidate = getattr(bare, "apply_spacing", None)
            if callable(candidate):
                apply_fn = candidate
    if apply_fn is None:
        mod_name = f"_typekernel_user_spacing_{abs(hash(str(root_resolved))) & 0xFFFFFFFF:x}"
        source = spacing_py.read_text(encoding="utf-8")
        code = compile(source, str(spacing_py), "exec")
        module = ModuleType(mod_name)
        module.__file__ = str(spacing_py)
        module.__loader__ = None
        module.__package__ = None
        sys.modules[mod_name] = module
        exec(code, module.__dict__)  # noqa: S102 - project spacing by design
        candidate = getattr(module, "apply_spacing", None)
        if callable(candidate):
            apply_fn = candidate
    if apply_fn is None:
        return
    apply_fn(font, system)
