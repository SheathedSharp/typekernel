"""Build a TTF from a UFO and record tool versions in a BuildManifest.

Delegates compilation to ``ufo2ft.compileTTF`` (fontmake sits on the same
stack). Does not invent hinting, custom OT writers, or contour filters —
``filters`` stays empty unless a caller records choices later.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any


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
    tt_font = ufo2ft.compileTTF(font, removeOverlaps=False)
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
        output_format="ttf",
    )
    if manifest_path is not None:
        manifest.write_json(manifest_path)
    return manifest
