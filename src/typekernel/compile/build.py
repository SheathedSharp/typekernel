"""Build OTF / TTF from a UFO and record tool versions in a BuildManifest.

Delegates compilation to ``ufo2ft.compileOTF`` / ``compileTTF`` (fontmake sits
on the same stack). Does not invent hinting, custom OT writers, or contour filters —
``filters`` stays empty unless a caller records choices later.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Literal

from typekernel.font.font import Font
from typekernel.font.masters import AXIS_NAMES, Master, axis_ranges, check_masters


def _pkg_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


@dataclass(frozen=True, slots=True)
class BuildManifest:
    """Record of which tools produced a font binary from a UFO.

    Attributes:
        fonttools_version: Installed fontTools version, if any.
        fontmake_version: Installed fontmake version, if any.
        ufo2ft_version: Installed ufo2ft version, if any.
        timestamp: UTC ISO-8601 time when the build finished.
        inputs: Paths that fed the build (UFO path, output path).
        filters: Contour / glyph filters requested for this build. Default
            empty — the compile bridge does not beautify.
        output_format: ``\"ttf\"`` or ``\"otf\"``.
    """

    fonttools_version: str | None
    fontmake_version: str | None
    ufo2ft_version: str | None
    timestamp: str
    inputs: dict[str, str]
    filters: tuple[str, ...] = ()
    output_format: str = "ttf"

    def to_json(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict (filters as a list)."""
        data = asdict(self)
        data["filters"] = list(self.filters)
        return data

    def write_json(self, path: str | Path) -> Path:
        """Write the manifest as UTF-8 JSON and return ``path``."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(self.to_json(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return out


OutputFormat = Literal["ttf", "otf", "woff2"]


def _build_woff2_from_ttf(
    ufo_path: str | Path,
    out_path: str | Path,
    *,
    manifest_path: str | Path | None = None,
) -> BuildManifest:
    """Compile UFO to TTF in memory, then write WOFF2."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        ttf = Path(tmp) / "tmp.ttf"
        manifest = build_binary_from_ufo(ufo_path, ttf, "ttf")
    from fontTools.ttLib import TTFont

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tt = TTFont(ttf)
    tt.flavor = "woff2"
    tt.save(out)
    woff_manifest = replace(manifest, output_format="woff2", inputs={**manifest.inputs, "output": str(out)})
    if manifest_path is not None:
        woff_manifest.write_json(manifest_path)
    return woff_manifest


def build_ttf_from_ufo(
    ufo_path: str | Path,
    out_path: str | Path,
    *,
    manifest_path: str | Path | None = None,
) -> BuildManifest:
    """Compile ``ufo_path`` to a TTF at ``out_path`` via ufo2ft.

    Uses ``ufo2ft.compileTTF`` with ``removeOverlaps=False`` so the bridge does
    not secretly rewrite contours. Cubic→quadratic conversion for TrueType is
    the normal compile boundary (fontTools cu2qu), not a design beautify.

    Requires the optional ``compile`` extra (``ufoLib2`` + ``ufo2ft``).
    ``fontmake`` may also be installed; its version is recorded when present.

    Returns:
        A :class:`BuildManifest` describing the tools used. When
        ``manifest_path`` is set, the same record is also written as JSON.
    """
    return build_binary_from_ufo(ufo_path, out_path, "ttf", manifest_path=manifest_path)


def build_binary_from_ufo(
    ufo_path: str | Path,
    out_path: str | Path,
    output_format: OutputFormat,
    *,
    manifest_path: str | Path | None = None,
) -> BuildManifest:
    """Compile ``ufo_path`` to ``output_format`` (``"ttf"`` or ``"otf"``).

    OTF keeps cubic outlines (CFF); TTF converts to quadratics at the compile
    boundary. Both use ``removeOverlaps=False``. Kerning, groups, anchors and
    ``features.fea`` in the UFO become GPOS/GSUB through ufo2ft's feature
    writers.
    """
    if output_format not in ("ttf", "otf", "woff2"):
        raise ValueError(f"output_format must be 'ttf', 'otf', or 'woff2', got {output_format!r}")
    if output_format == "woff2":
        return _build_woff2_from_ttf(ufo_path, out_path, manifest_path=manifest_path)
    ufo = Path(ufo_path)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    try:
        import ufoLib2
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "build_ttf_from_ufo requires the optional 'compile' extra "
            "(pip install 'typekernel[compile]')"
        ) from exc

    try:
        import ufo2ft
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "build_ttf_from_ufo requires ufo2ft "
            "(pip install 'typekernel[compile]')"
        ) from exc

    font = ufoLib2.Font.open(ufo)
    # Explicit thin defaults: no overlap removal, no extra filters.
    compiler = ufo2ft.compileTTF if output_format == "ttf" else ufo2ft.compileOTF
    tt_font = compiler(font, removeOverlaps=False)
    tt_font.save(out)

    manifest = BuildManifest(
        fonttools_version=_pkg_version("fonttools"),
        fontmake_version=_pkg_version("fontmake"),
        ufo2ft_version=_pkg_version("ufo2ft"),
        timestamp=datetime.now(UTC).isoformat(),
        inputs={
            "ufo": str(ufo),
            "output": str(out),
        },
        filters=(),
        output_format=output_format,
    )
    if manifest_path is not None:
        manifest.write_json(manifest_path)
    return manifest


@dataclass(frozen=True, slots=True)
class FontBuild:
    """Files produced by :func:`build_font`."""

    ufo: Path
    binaries: dict[str, Path]
    manifests: dict[str, BuildManifest]


def _file_stem(font: Font) -> str:
    raw = f"{font.info.family_name}-{font.info.style_name}"
    return "".join(ch for ch in raw if ch.isalnum() or ch in "-_")


def build_font(
    font: Font,
    out_dir: str | Path,
    *,
    formats: Sequence[OutputFormat] = ("otf", "ttf"),
    file_stem: str | None = None,
) -> FontBuild:
    """Validate, write ``<stem>.ufo``, then compile each format into ``out_dir``.

    Rebuilding replaces previous outputs with the same stem. Each binary gets
    a ``<stem>.<format>.manifest.json`` next to it.
    """
    from typekernel.compile.ufo_export import write_font_to_ufo

    out = Path(out_dir)
    stem = file_stem or _file_stem(font)
    ufo_path = write_font_to_ufo(font, out / f"{stem}.ufo", overwrite=True)
    binaries: dict[str, Path] = {}
    manifests: dict[str, BuildManifest] = {}
    for fmt in formats:
        binary = out / f"{stem}.{fmt}"
        manifests[fmt] = build_binary_from_ufo(
            ufo_path, binary, fmt, manifest_path=out / f"{stem}.{fmt}.manifest.json"
        )
        binaries[fmt] = binary
    return FontBuild(ufo=ufo_path, binaries=binaries, manifests=manifests)


@dataclass(frozen=True, slots=True)
class VariableFontBuild:
    """Files produced by :func:`build_variable_font`.

    ``warnings`` lists fontTools interpolation findings that do not stop a
    build (kinks, under/overweight midpoints) for a designer to review.
    """

    designspace: Path
    masters: tuple[Path, ...]
    binaries: dict[str, Path]
    manifests: dict[str, BuildManifest]
    warnings: tuple[str, ...] = ()


STRUCTURAL_PROBLEMS = frozenset(
    {
        "missing",
        "open_path",
        "path_count",
        "node_count",
        "node_incompatibility",
        "contour_order",
        "wrong_start_point",
    }
)
"""fontTools interpolation findings that make masters unusable."""


def deep_check_masters(
    ufo_paths: Sequence[str | Path], names: Sequence[str]
) -> tuple[list[str], list[str]]:
    """Run ``fontTools.varLib.interpolatable`` over master UFOs.

    Catches what a segment-kind comparison cannot: wrong start points and
    contour order. Returns ``(errors, warnings)``; errors are
    :data:`STRUCTURAL_PROBLEMS`, warnings the quality findings.
    """
    import ufoLib2
    from fontTools.varLib.interpolatable import test

    fonts = [ufoLib2.Font.open(p) for p in ufo_paths]
    glyphsets = [{glyph.name: glyph for glyph in font} for font in fonts]
    errors: list[str] = []
    warnings: list[str] = []
    for glyph, problems in sorted(test(glyphsets, names=list(names)).items()):
        for p in problems:
            kind = p["type"]
            where = f"{p.get('master_1', '?')}→{p.get('master_2', '?')}"
            contour = f" contour {p['contour']}" if "contour" in p else ""
            line = f"glyph {glyph!r}{contour}: {kind} ({where})"
            (errors if kind in STRUCTURAL_PROBLEMS else warnings).append(line)
    return errors, warnings


def write_masters_designspace(
    masters: Sequence[Master], out_dir: str | Path, *, file_stem: str | None = None
) -> tuple[Path, tuple[Path, ...]]:
    """Write each master as a UFO plus a ``.designspace`` tying them together.

    Axes span the masters' locations with the first master as the default.
    Every master also becomes a named instance (``fvar``). Raises
    ``ValueError`` if :func:`~typekernel.font.check_masters` reports problems.
    """
    from fontTools.designspaceLib import (
        AxisDescriptor,
        DesignSpaceDocument,
        InstanceDescriptor,
        SourceDescriptor,
    )

    from typekernel.compile.ufo_export import write_font_to_ufo

    problems = check_masters(masters)
    if problems:
        raise ValueError("masters are not compatible:\n  " + "\n  ".join(problems))

    out = Path(out_dir)
    family = masters[0].font
    stem = file_stem or _file_stem(family).rsplit("-", 1)[0]
    doc = DesignSpaceDocument()
    names = {tag: AXIS_NAMES.get(tag, tag) for tag in masters[0].location}
    for tag, (lo, default, hi) in axis_ranges(masters).items():
        axis = AxisDescriptor()
        axis.tag, axis.name = tag, names[tag]
        axis.minimum, axis.default, axis.maximum = lo, default, hi
        axis.labelNames = {"en": names[tag]}
        doc.addAxis(axis)

    ufo_paths: list[Path] = []
    for m in masters:
        style = "".join(ch for ch in m.style_name if ch.isalnum() or ch in "-_")
        ufo_path = write_font_to_ufo(m.font, out / "masters" / f"{stem}-{style}.ufo", overwrite=True)
        ufo_paths.append(ufo_path)
        source = SourceDescriptor()
        source.filename = str(ufo_path.relative_to(out))
        source.name = m.style_name
        source.familyName = family.info.family_name
        source.styleName = m.style_name
        source.location = {names[tag]: v for tag, v in m.location.items()}
        doc.addSource(source)

    tags = list(masters[0].location)
    for m in sorted(masters, key=lambda m: [m.location[t] for t in tags]):
        instance = InstanceDescriptor()
        instance.familyName = family.info.family_name
        instance.styleName = m.style_name
        instance.location = {names[tag]: v for tag, v in m.location.items()}
        doc.addInstance(instance)

    path = out / f"{stem}.designspace"
    out.mkdir(parents=True, exist_ok=True)
    doc.write(path)
    return path, tuple(ufo_paths)


def build_variable_font(
    masters: Sequence[Master],
    out_dir: str | Path,
    *,
    formats: Sequence[OutputFormat] = ("ttf",),
    file_stem: str | None = None,
) -> VariableFontBuild:
    """Check, write UFO masters + designspace, then compile a variable font.

    Masters pass :func:`~typekernel.font.check_masters` and then
    :func:`deep_check_masters` (fontTools) before compiling. ``"ttf"`` builds
    TrueType outlines with ``gvar``; ``"otf"`` builds CFF2. Outputs are
    ``<stem>-VF.<format>`` with a manifest next to each.
    """
    try:
        import ufo2ft
        import ufoLib2
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "build_variable_font requires the optional 'compile' extra "
            "(pip install 'typekernel[compile]')"
        ) from exc
    from fontTools.designspaceLib import DesignSpaceDocument

    out = Path(out_dir)
    ds_path, ufo_paths = write_masters_designspace(masters, out, file_stem=file_stem)
    errors, warnings = deep_check_masters(ufo_paths, [m.style_name for m in masters])
    if errors:
        raise ValueError("masters do not interpolate:\n  " + "\n  ".join(errors))
    stem = ds_path.stem
    binaries: dict[str, Path] = {}
    manifests: dict[str, BuildManifest] = {}
    for fmt in formats:
        if fmt not in ("ttf", "otf", "woff2"):
            raise ValueError(f"output_format must be 'ttf', 'otf', or 'woff2', got {fmt!r}")
        doc = DesignSpaceDocument.fromfile(ds_path)
        doc.loadSourceFonts(ufoLib2.Font.open)
        if fmt == "woff2":
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                ttf = Path(tmp) / "vf.ttf"
                ufo2ft.compileVariableTTF(doc).save(ttf)
                from fontTools.ttLib import TTFont

                binary = out / f"{stem}-VF.woff2"
                tt = TTFont(ttf)
                tt.flavor = "woff2"
                tt.save(binary)
        else:
            compiler = ufo2ft.compileVariableTTF if fmt == "ttf" else ufo2ft.compileVariableCFF2
            binary = out / f"{stem}-VF.{fmt}"
            compiler(doc).save(binary)
        manifest = BuildManifest(
            fonttools_version=_pkg_version("fonttools"),
            fontmake_version=_pkg_version("fontmake"),
            ufo2ft_version=_pkg_version("ufo2ft"),
            timestamp=datetime.now(UTC).isoformat(),
            inputs={"designspace": str(ds_path), "output": str(binary)},
            filters=(),
            output_format=fmt,
        )
        manifest.write_json(out / f"{stem}-VF.{fmt}.manifest.json")
        binaries[fmt] = binary
        manifests[fmt] = manifest
    return VariableFontBuild(ds_path, ufo_paths, binaries, manifests, tuple(warnings))
