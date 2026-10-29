"""Load a user project directory via :class:`~typekernel.project.ProjectSession`."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType
from typing import cast

from typekernel.font.font import Font
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
    """Open ``root`` briefly and return its :class:`~typekernel.project.Project`.

    Prefer :func:`open_project` / :class:`~typekernel.project.ProjectSession`
    when evaluating glyphs — this helper exists for call sites that only need
    the Project declaration. The session's isolation is used during the load
    so ``system`` / ``elements`` from another project cannot leak in.
    """
    with open_project(root) as session:
        project = session.project
        # Detach a stable Project: specs already discovered; keep corners/ends.
        # Callers that later call discover()/evaluate() use Project's own loader
        # (unit-test path). CLI paths should keep the session open instead.
        return cast(Project, project)


def build_font_from_session(
    session: ProjectSession,
    *,
    family_name: str,
    style_name: str = "Regular",
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
    font = Font.from_system(system, family_name, style_name)
    for name in session.specs():
        font.add_glyph(session.glyph(name, master=master), replace=True)
    if apply_spacing:
        apply_project_spacing_with_system(font, system, session.root)
    return font


def apply_project_spacing(font: Font, project: Project, project_root: Path) -> None:
    """If ``project_root/spacing.py`` defines ``apply_spacing``, run it."""
    apply_project_spacing_with_system(font, project.system, project_root)


def build_font_from_project(
    project: Project,
    *,
    family_name: str,
    style_name: str = "Regular",
    project_root: str | Path | None = None,
    apply_spacing: bool = True,
    master: str | None = None,
) -> Font:
    """Discover glyphs and assemble a :class:`~typekernel.font.Font`.

    When ``project_root`` is set, prefer opening a :class:`ProjectSession` so
    imports stay isolated. Falls back to ``project.discover()`` for in-memory
    projects (no on-disk root).
    """
    root = Path(project_root).resolve() if project_root is not None else None
    if root is None:
        # Infer from glyphs parent when it looks like a real project tree.
        candidate = Path(project._glyphs).resolve().parent
        if (candidate / "font.py").is_file() or (candidate / "project.py").is_file():
            root = candidate

    if root is not None and (
        (root / "font.py").is_file() or (root / "project.py").is_file()
    ):
        with open_project(root) as session:
            return build_font_from_session(
                session,
                family_name=family_name,
                style_name=style_name,
                apply_spacing=apply_spacing,
                master=master,
            )

    project.discover()
    system = project.system
    if master is not None:
        by_name = {m.name: m for m in project.masters}
        if master not in by_name:
            raise KeyError(f"unknown master {master!r}")
        system = by_name[master].system
    font = Font.from_system(system, family_name, style_name)
    for name in project.specs():
        font.add_glyph(project.to_glyph(name, master=master), replace=True)
    if apply_spacing and root is not None:
        apply_project_spacing_with_system(font, system, root)
    return font


def apply_project_spacing_with_system(font: Font, system: System, project_root: Path) -> None:
    """Like :func:`apply_project_spacing` but with an explicit System (masters).

    Loads ``spacing.py`` under a unique module name. When a ProjectSession is
    active for this root, the session alias already provides ``spacing``; we
    still exec via a unique name so repeated calls see fresh source without
    deleting ``__pycache__``.
    """
    spacing_py = Path(project_root) / "spacing.py"
    if not spacing_py.is_file():
        return
    root_s = str(Path(project_root).resolve())
    # Prefer the live session alias when present (isolated load).
    apply_fn = None
    bare = sys.modules.get("spacing")
    if bare is not None:
        bare_file = getattr(bare, "__file__", "") or ""
        if bare_file and Path(bare_file).resolve().parent == Path(project_root).resolve():
            apply_fn = getattr(bare, "apply_spacing", None)
    if apply_fn is None:
        mod_name = f"_typekernel_user_spacing_{abs(hash(root_s)) & 0xFFFFFFFF:x}"
        # Always re-exec from source so same-second edits are visible (no pyc race).
        source = spacing_py.read_text(encoding="utf-8")
        code = compile(source, str(spacing_py), "exec")
        module = ModuleType_safe(mod_name, spacing_py)
        sys.modules[mod_name] = module
        exec(code, module.__dict__)  # noqa: S102 - project spacing by design
        apply_fn = getattr(module, "apply_spacing", None)
    if apply_fn is None:
        return
    apply_fn(font, system)


def ModuleType_safe(name: str, path: Path) -> ModuleType:
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__loader__ = None
    module.__package__ = None
    return module
