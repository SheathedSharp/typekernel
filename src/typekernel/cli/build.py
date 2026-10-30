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
from typekernel.project import open_project

__all__ = ["build_font_from_project", "build_project", "build_variable_project"]




def apply_italic_face_metadata(binary: Path, *, family: str, style_name: str) -> None:
    """Write STAT ital + italicAngle/fsSelection for ``FamilyInfo.italic`` faces."""
    from fontTools.ttLib import TTFont

    from typekernel.axes.family import (
        FamilyMember,
        FamilySpec,
        apply_family_names,
        apply_family_stat,
    )

    tt = TTFont(binary)
    member = FamilyMember(style_name=style_name or "Italic", italic=True)
    spec = FamilySpec(name=family, members=(member,))
    apply_family_names(tt, spec, member)
    apply_family_stat(tt, spec, member)
    tt.save(binary)


def build_project(
    root: str | Path,
    *,
    out_dir: str | Path | None = None,
    formats: tuple[OutputFormat, ...] = ("otf",),
    resolve_overlaps: bool = False,
) -> tuple[Font, FontBuild]:
    """Load ``root``, assemble glyphs, write binaries under ``out_dir``."""
    from typekernel.cli.doctor import require_compile_extras

    require_compile_extras(context="tk build")
    root_path = Path(root).resolve()
    with open_project(root_path) as session:
        font = build_font_from_session(session)
        info = session.project.info
        style = session.project.style_name
    dest = Path(out_dir) if out_dir is not None else root_path / "build"
    result = build_font(font, dest, formats=formats, resolve_overlaps=resolve_overlaps)
    if info.italic:
        for path in result.binaries.values():
            if path.suffix.lower() in {".otf", ".ttf"}:
                apply_italic_face_metadata(
                    Path(path), family=info.family, style_name=style
                )
    return font, result


def build_variable_project(
    root: str | Path,
    *,
    out_dir: str | Path | None = None,
    formats: tuple[OutputFormat, ...] = ("ttf",),
) -> tuple[list[FontMaster], VariableFontBuild]:
    """Build masters from ``Project.masters`` and compile a variable font."""
    root_path = Path(root).resolve()
    with open_project(root_path) as session:
        project = session.project
        family = project.info.family
        defaults = {
            "Light": {"wght": 300.0},
            "Regular": {"wght": 400.0},
            "Bold": {"wght": 700.0},
        }

        styles: list[tuple[str, str | None]] = [("Regular", None)]
        for m in project.masters:
            styles.append((m.name, m.name))

        font_masters: list[FontMaster] = []
        for style_name, master_key in styles:
            font = build_font_from_session(
                session,
                family_name=family,
                style_name=style_name,
                master=master_key,
            )
            if master_key is None:
                location = defaults.get("Regular", {"wght": 400.0})
            else:
                spec = next(m for m in project.masters if m.name == master_key)
                location = dict(spec.location) or defaults.get(master_key) or {"wght": 400.0}
            font_masters.append(FontMaster(location=location, font=font, name=style_name))

    dest = Path(out_dir) if out_dir is not None else root_path / "build"
    axes = tuple(project.axes) if project.axes else None
    instances = tuple(project.instances) if project.instances else None
    result = build_variable_font(
        font_masters,
        dest,
        formats=formats,
        axes=axes,
        instances=instances,
    )
    return font_masters, result
