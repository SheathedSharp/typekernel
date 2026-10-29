"""Thin UFO export: a :class:`~typekernel.font.Font` (or one outline) → UFO3.

Uses ufoLib2 for the document and the existing geo pen bridge
(:func:`typekernel.geo.pens.draw_outline`) so coordinates are replayed as
``moveTo`` / ``lineTo`` / ``curveTo`` without resampling or beautifying.
"""

from __future__ import annotations

import math
import shutil
from pathlib import Path
from typing import Any

from typekernel.font.font import Font
from typekernel.geo.outline import Outline
from typekernel.geo.pens import draw_outline

DEFAULT_UNITS_PER_EM = 1000
DEFAULT_ADVANCE_WIDTH = 600


def _import_ufolib2() -> Any:
    try:
        import ufoLib2
    except ImportError as exc:  # pragma: no cover - exercised when extra missing
        raise ImportError(
            "UFO export requires the optional 'compile' extra "
            "(pip install 'typekernel[compile]')"
        ) from exc
    return ufoLib2


def _prepare_path(path: str | Path, overwrite: bool) -> Path:
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
    return out


def font_to_ufo(font: Font) -> Any:
    """Build an in-memory ``ufoLib2.Font`` from ``font``.

    Writes every glyph (outline, components, anchors, unicodes, width), glyph
    order, kerning groups and pairs, ``features.fea`` and fontinfo. Windows
    ascent/descent are widened to the drawn bounds so no ink is clipped.

    Raises:
        ValueError: if :meth:`Font.validate` reports problems.
    """
    problems = font.validate()
    if problems:
        raise ValueError("font failed validation:\n  " + "\n  ".join(problems))

    ufoLib2 = _import_ufolib2()
    from ufoLib2.objects import Anchor as UfoAnchor

    ufo = ufoLib2.Font()
    for key, value in font.info.to_ufo_attributes().items():
        setattr(ufo.info, key, value)

    for name in font.glyph_order:
        g = font[name]
        ug = ufo.newGlyph(name)
        ug.width = g.advance
        ug.unicodes = list(g.unicodes)
        pen = ug.getPen()
        draw_outline(g.outline, pen)
        for comp in g.components:
            pen.addComponent(comp.base, comp.transform)
        for a in g.anchors:
            ug.anchors.append(UfoAnchor(a.x, a.y, a.name))
    ufo.lib["public.glyphOrder"] = font.glyph_order

    for group, members in font.groups.items():
        ufo.groups[group] = list(members)
    for (left, right), value in font.kerning.items():
        ufo.kerning[(left, right)] = value
    if font.features:
        ufo.features.text = font.features

    y_max, y_min = 0.0, 0.0
    layer = ufo.layers.defaultLayer
    for ug in ufo:
        box = ug.getBounds(layer)
        if box is not None:
            y_min = min(y_min, box.yMin)
            y_max = max(y_max, box.yMax)
    ufo.info.openTypeOS2WinAscent = max(ufo.info.ascender, math.ceil(y_max))
    ufo.info.openTypeOS2WinDescent = max(-ufo.info.descender, math.ceil(-y_min))
    return ufo


def write_font_to_ufo(font: Font, path: str | Path, *, overwrite: bool = False) -> Path:
    """Write ``font`` as a UFO3 directory and return its path.

    Raises ``FileExistsError`` if ``path`` exists unless ``overwrite=True``.
    Requires the optional ``compile`` extra (``ufoLib2``).
    """
    ufo = font_to_ufo(font)
    out = _prepare_path(path, overwrite)
    ufo.save(out)
    return out


def write_outline_to_ufo(
    outline: Outline,
    path: str | Path,
    *,
    glyph_name: str = "glyph",
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
    ufoLib2 = _import_ufolib2()

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

    out = _prepare_path(path, overwrite)
    font.save(out)
    return out
