"""Load a user project directory into a :class:`~typekernel.project.Project`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from typekernel.font.font import Font
from typekernel.project import Project
from typekernel.system import System

__all__ = ["apply_project_spacing", "apply_project_spacing_with_system", "build_font_from_project", "load_project"]

def _purge_project_local_modules(project_root: Path | None = None) -> None:
    """Drop bare ``system`` / ``elements`` / ``spacing`` so the next project root wins.

    Starter ``font.py`` does ``from system import …``. Concurrent or sequential
    tests that load different project roots would otherwise reuse the first
    ``system`` module left on ``sys.modules``.

    Also clears that root's ``__pycache__`` for those modules so same-second
    edits are not masked by stale ``.pyc`` (needed for ``tk diff`` / in-process
    rebuild loops).
    """
    import importlib

    for bare in ("system", "elements", "spacing", "font"):
        sys.modules.pop(bare, None)
    importlib.invalidate_caches()
    if project_root is None:
        return
    cache = Path(project_root) / "__pycache__"
    if not cache.is_dir():
        return
    for bare in ("system", "elements", "spacing", "font"):
        for pyc in cache.glob(f"{bare}.cpython-*.pyc"):
            pyc.unlink(missing_ok=True)



def load_project(root: str | Path) -> Project:
    """Import ``font.py`` from ``root`` and return its Project.

    ``font.py`` must define ``get_project() -> Project`` or a ``project``
    attribute (instance or zero-arg callable).
    """
    root_path = Path(root).resolve()
    font_py = root_path / "font.py"
    if not font_py.is_file():
        raise FileNotFoundError(f"no font.py in project root: {root_path}")

    root_s = str(root_path)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)

    _purge_project_local_modules(root_path)

    # Unique module name so multiple projects / reloads do not clash.
    mod_name = f"_typekernel_user_font_{abs(hash(root_s)) & 0xFFFFFFFF:x}"
    spec = importlib.util.spec_from_file_location(mod_name, font_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {font_py}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)

    if hasattr(module, "get_project"):
        project = module.get_project()
    elif hasattr(module, "project"):
        project = module.project() if callable(module.project) else module.project
    else:
        raise AttributeError(f"{font_py} must define get_project() or project")
    if not isinstance(project, Project):
        raise TypeError(f"expected Project, got {type(project)!r}")
    return project


def apply_project_spacing(font: Font, project: Project, project_root: Path) -> None:
    """If ``project_root/spacing.py`` defines ``apply_spacing``, run it.

    Starter / user spacing is project code (ARCHITECTURE.md「核心概念」) — not kernel
    letter builders. Missing file is a no-op so empty scaffolds still build.
    """
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

    When ``project_root`` is set (or inferred from ``project`` glyphs parent)
    and ``apply_spacing`` is true, load optional ``spacing.py`` so advances /
    LSB / RSB are metrics-key based rather than bbox-only.

    ``master`` selects a Project master System (and per-glyph overrides) for
    Light/Bold evaluation; default ``None`` uses the project's base system.
    """
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
    if apply_spacing:
        root = Path(project_root) if project_root is not None else Path(project._glyphs).resolve().parent
        # Pack with the master's stem values so bearings track weight.
        # Temporarily swap project.system view: apply_spacing takes system arg.
        apply_project_spacing_with_system(font, system, root)
    return font


def apply_project_spacing_with_system(font: Font, system: System, project_root: Path) -> None:
    """Like :func:`apply_project_spacing` but with an explicit System (masters)."""
    spacing_py = project_root / "spacing.py"
    if not spacing_py.is_file():
        return
    root_s = str(project_root.resolve())
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    mod_name = f"_typekernel_user_spacing_{abs(hash(root_s)) & 0xFFFFFFFF:x}"
    spec = importlib.util.spec_from_file_location(mod_name, spacing_py)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {spacing_py}")
    module = sys.modules.get(mod_name)
    if module is None:
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    apply_fn = getattr(module, "apply_spacing", None)
    if apply_fn is None:
        return
    apply_fn(font, system)
