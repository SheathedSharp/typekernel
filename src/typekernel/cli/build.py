"""``tk build`` — Project → Font → UFO/OTF/TTF / variable font."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.load import build_font_from_project, build_font_from_session
from typekernel.compile.build import (
    FontBuild,
    OutputFormat,
    VariableFontBuild,
    build_font,
    build_variable_font,
)
from typekernel.font.font import Font
from typekernel.font.masters import Master as FontMaster
from typekernel.project import ProjectSession, open_project

__all__ = ["build_font_from_project", "build_project", "build_variable_project"]


def _family_and_style_from_session(session: ProjectSession) -> tuple[str, str]:
    """Read FAMILY_NAME / STYLE_NAME from the loaded system module when present."""
    family = session.root.name
    style = "Regular"
    project = session.project
    # P1-2: FamilyInfo on Project; until then fall back to system module attrs.
    info = getattr(project, "info", None)
    if info is not None:
        family = getattr(info, "family", family) or family
    system_mod = None
    import sys

    bare = sys.modules.get("system")
    if bare is not None:
        bare_file = getattr(bare, "__file__", "") or ""
        if bare_file and Path(bare_file).resolve().parent == session.root:
            system_mod = bare
    if system_mod is not None:
        family = str(getattr(system_mod, "FAMILY_NAME", family))
        style = str(getattr(system_mod, "STYLE_NAME", style))
    return family, style


def _master_locations_from_session(session: ProjectSession) -> dict[str, dict[str, float]]:
    import sys

    bare = sys.modules.get("system")
    if bare is None:
        return {}
    bare_file = getattr(bare, "__file__", "") or ""
    if not bare_file or Path(bare_file).resolve().parent != session.root:
        return {}
    locs = getattr(bare, "MASTER_LOCATIONS", None)
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
    with open_project(root_path) as session:
        family, style = _family_and_style_from_session(session)
        font = build_font_from_session(
            session, family_name=family, style_name=style
        )
    dest = Path(out_dir) if out_dir is not None else root_path / "build"
    result = build_font(font, dest, formats=formats, resolve_overlaps=resolve_overlaps)
    return font, result


def build_variable_project(
    root: str | Path,
    *,
    out_dir: str | Path | None = None,
    formats: tuple[OutputFormat, ...] = ("ttf",),
) -> tuple[list[FontMaster], VariableFontBuild]:
    """Build Light / Regular / Bold (etc.) masters and compile a variable font.

    Uses Project masters plus the base Regular system. Axis locations come from
    ``MASTER_LOCATIONS`` in system.py when present; otherwise wght 300/400/700
    for Light/Regular/Bold.
    """
    root_path = Path(root).resolve()
    with open_project(root_path) as session:
        family, _style = _family_and_style_from_session(session)
        locs = _master_locations_from_session(session)
        defaults = {
            "Light": {"wght": 300.0},
            "Regular": {"wght": 400.0},
            "Bold": {"wght": 700.0},
        }

        styles: list[tuple[str, str | None]] = [("Regular", None)]
        for m in session.project.masters:
            styles.append((m.name, m.name))

        font_masters: list[FontMaster] = []
        for style_name, master_key in styles:
            font = build_font_from_session(
                session,
                family_name=family,
                style_name=style_name,
                master=master_key,
            )
            location = locs.get(style_name) or defaults.get(style_name) or {"wght": 400.0}
            font_masters.append(FontMaster(location=location, font=font, name=style_name))

    dest = Path(out_dir) if out_dir is not None else root_path / "build"
    result = build_variable_font(font_masters, dest, formats=formats)
    return font_masters, result
