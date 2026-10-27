"""Load a user project directory into a :class:`~typekernel.project.Project`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from typekernel.font.font import Font
from typekernel.project import Project

__all__ = ["build_font_from_project", "load_project"]


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


def build_font_from_project(
    project: Project,
    *,
    family_name: str,
    style_name: str = "Regular",
) -> Font:
    """Discover glyphs and assemble a :class:`~typekernel.font.Font`."""
    project.discover()
    font = Font.from_system(project.system, family_name, style_name)
    for name in project.specs():
        font.add_glyph(project.to_glyph(name), replace=True)
    return font

