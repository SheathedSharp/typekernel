"""Thin UFO export: one outline becomes one glyph in a UFO3 font.

Uses ufoLib2 for the document and the existing geo pen bridge
(:func:`typekernel.geo.pens.draw_outline`) so coordinates are replayed as
``moveTo`` / ``lineTo`` / ``curveTo`` without resampling or beautifying.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from typekernel.geo.outline import Outline
from typekernel.geo.pens import draw_outline

DEFAULT_UNITS_PER_EM = 1000
DEFAULT_ADVANCE_WIDTH = 600


def write_outline_to_ufo(
    outline: Outline,
    path: str | Path,
    *,
    glyph_name: str = "A",
    units_per_em: int = DEFAULT_UNITS_PER_EM,
    advance_width: int = DEFAULT_ADVANCE_WIDTH,
    family_name: str = "TypekernelExport",
    style_name: str = "Regular",
    overwrite: bool = False,
) -> Path:
    """Write a minimal UFO3 containing a single glyph drawn from ``outline``.

    The outline is drawn through :func:`draw_outline` into the glyph's pen.
    No optical transforms, no overlap removal, no point rounding beyond what
    the caller already applied.

    If ``path`` already exists, raises ``FileExistsError`` unless
    ``overwrite=True``, in which case the existing UFO directory (or file) is
    removed first.

    Requires the optional ``compile`` extra (``ufoLib2``).

    Returns:
        The directory path of the written UFO.
    """
    try:
        import ufoLib2
    except ImportError as exc:  # pragma: no cover - exercised when extra missing
        raise ImportError(
            "write_outline_to_ufo requires the optional 'compile' extra "
            "(pip install 'typekernel[compile]')"
        ) from exc

    font = ufoLib2.Font()
    font.info.unitsPerEm = int(units_per_em)
    font.info.familyName = family_name
    font.info.styleName = style_name
    # Vertical metrics: minimal values so downstream fontmake/ufo2ft can build.
    font.info.ascender = int(units_per_em * 0.8)
    font.info.descender = int(-units_per_em * 0.2)
    font.info.xHeight = int(units_per_em * 0.5)
    font.info.capHeight = int(units_per_em * 0.7)

    glyph = font.newGlyph(glyph_name)
    glyph.width = int(advance_width)
    draw_outline(outline, glyph.getPen())

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        if not overwrite:
            raise FileExistsError(
                f"UFO path already exists: {out} (pass overwrite=True to replace)"
            )
        if out.is_dir():
            shutil.rmtree(out)
        else:
            out.unlink()
    font.save(out)
    return out
