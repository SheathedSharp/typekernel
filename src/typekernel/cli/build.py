"""``tk build`` — Project → Font → UFO/OTF/TTF / variable font."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from typekernel.cli.load import build_font_from_project, load_project
from typekernel.compile.build import FontBuild, OutputFormat, build_font, build_variable_font
from typekernel.font.font import Font
from typekernel.font.masters import Master as FontMaster

__all__ = ["build_project", "build_variable_project"]


def _family_and_style(root: Path) -> tuple[str, str]:
    system_py = root / "system.py"
    family = root.name
    style = "Regular"
    if system_py.is_file():
        mod_name = f"_typekernel_user_system_{abs(hash(str(root.resolve()))) & 0xFFFFFFFF:x}"
        spec = importlib.util.spec_from_file_location(mod_name, system_py)
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            root_s = str(root.resolve())
            if root_s not in sys.path:
                sys.path.insert(0, root_s)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            family = str(getattr(module, "FAMILY_NAME", family))
            style = str(getattr(module, "STYLE_NAME", style))
    return family, style


def _load_master_locations(root: Path) -> dict[str, dict[str, float]]:
    """Optional ``MASTER_LOCATIONS`` from system.py (name → axis location)."""
    system_py = root / "system.py"
    if not system_py.is_file():
        return {}
    mod_name = f"_typekernel_user_system_loc_{abs(hash(str(root.resolve()))) & 0xFFFFFFFF:x}"
    if mod_name in sys.modules:
        module = sys.modules[mod_name]
    else:
        spec = importlib.util.spec_from_file_location(mod_name, system_py)
        if spec is None or spec.loader is None:
            return {}
        module = importlib.util.module_from_spec(spec)
        root_s = str(root.resolve())
        if root_s not in sys.path:
            sys.path.insert(0, root_s)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
    locs = getattr(module, "MASTER_LOCATIONS", None)
    return dict(locs) if locs else {}


def build_project(
    root: str | Path,
    *,
    out_dir: str | Path | None = None,
    formats: tuple[OutputFormat, ...] = ("otf",),
    resolve_overlaps: bool = False,
) -> tuple[Font, FontBuild]:
    """Load ``root``, assemble glyphs, write binaries under ``out_dir``.

    ``resolve_overlaps`` unions ink at the static compile step (ufo2ft). Keep
    False for design/VF masters — overlaps are intentional there.
    """
    root_path = Path(root).resolve()
    project = load_project(root_path)
    family, style = _family_and_style(root_path)
    font = build_font_from_project(
        project, family_name=family, style_name=style, project_root=root_path
    )
    dest = Path(out_dir) if out_dir is not None else root_path / "build"
    result = build_font(font, dest, formats=formats, resolve_overlaps=resolve_overlaps)
    return font, result


def build_variable_project(
    root: str | Path,
    *,
    out_dir: str | Path | None = None,
    formats: tuple[str, ...] = ("ttf",),
) -> tuple[list[FontMaster], object]:
    """Build Light / Regular / Bold (etc.) masters and compile a variable font.

    Uses Project masters plus the base Regular system. Axis locations come from
    ``MASTER_LOCATIONS`` in system.py when present; otherwise wght 300/400/700
    for Light/Regular/Bold.
    """
    root_path = Path(root).resolve()
    project = load_project(root_path)
    family, _style = _family_and_style(root_path)
    locs = _load_master_locations(root_path)
    defaults = {
        "Light": {"wght": 300.0},
        "Regular": {"wght": 400.0},
        "Bold": {"wght": 700.0},
    }

    # Regular = base system; named Project masters fill the rest.
    styles: list[tuple[str, str | None]] = [("Regular", None)]
    for m in project.masters:
        styles.append((m.name, m.name))

    font_masters: list[FontMaster] = []
    for style_name, master_key in styles:
        font = build_font_from_project(
            project,
            family_name=family,
            style_name=style_name,
            project_root=root_path,
            master=master_key,
        )
        location = locs.get(style_name) or defaults.get(style_name) or {"wght": 400.0}
        font_masters.append(FontMaster(location=location, font=font, name=style_name))

    dest = Path(out_dir) if out_dir is not None else root_path / "build"
    result = build_variable_font(font_masters, dest, formats=formats)
    return font_masters, result
