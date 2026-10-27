"""``tk build`` — Project → Font → UFO/OTF/TTF."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from typekernel.cli.load import build_font_from_project, load_project
from typekernel.compile.build import FontBuild, OutputFormat, build_font
from typekernel.font.font import Font

__all__ = ["build_project"]


def _family_and_style(root: Path) -> tuple[str, str]:
    system_py = root / "system.py"
    family = root.name
    style = "Regular"
    if system_py.is_file():
        mod_name = f"_typekernel_user_system_{abs(hash(str(root.resolve()))) & 0xFFFFFFFF:x}"
        spec = importlib.util.spec_from_file_location(mod_name, system_py)
        if spec is not None and spec.loader is not None:
            module = importlib.util.module_from_spec(spec)
            # system.py imports typekernel only; safe to exec for constants.
            root_s = str(root.resolve())
            if root_s not in sys.path:
                sys.path.insert(0, root_s)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)
            family = str(getattr(module, "FAMILY_NAME", family))
            style = str(getattr(module, "STYLE_NAME", style))
    return family, style


def build_project(
    root: str | Path,
    *,
    out_dir: str | Path | None = None,
    formats: tuple[OutputFormat, ...] = ("otf",),
) -> tuple[Font, FontBuild]:
    """Load ``root``, assemble glyphs, write binaries under ``out_dir``."""
    root_path = Path(root).resolve()
    project = load_project(root_path)
    family, style = _family_and_style(root_path)
    font = build_font_from_project(project, family_name=family, style_name=style)
    dest = Path(out_dir) if out_dir is not None else root_path / "build"
    result = build_font(font, dest, formats=formats)
    return font, result
