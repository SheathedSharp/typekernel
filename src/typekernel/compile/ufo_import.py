"""Read glyphs back from a UFO (manual edits round-trip)."""

from __future__ import annotations

from pathlib import Path

from fontTools.pens.recordingPen import RecordingPen

from typekernel.font import Font, Glyph
from typekernel.font.info import FontInfo
from typekernel.geo.outline import Outline
from typekernel.geo.path_builder import PathBuilder
from typekernel.parts.context import DesignContext

__all__ = ["read_font_from_ufo"]


def _outline_from_recording(rec: RecordingPen) -> Outline:
    b = PathBuilder()
    for op, args in rec.value:
        if op == "moveTo":
            b.moveTo(*args[0])
        elif op == "lineTo":
            b.lineTo(*args[0])
        elif op == "qCurveTo":
            continue  # compile boundary only; UFO should stay cubic
        elif op == "curveTo":
            b.curveTo(*args[0], *args[1], *args[2])
        elif op == "closePath":
            b.closePath()
        elif op == "endPath":
            pass
    return b.build()


def read_font_from_ufo(
    ufo_path: str | Path,
    *,
    context: DesignContext | None = None,
) -> Font:
    """Load glyph outlines and metrics from a UFO3 directory."""
    try:
        import ufoLib2
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "read_font_from_ufo requires ufoLib2 (pip install 'typekernel[compile]')"
        ) from exc

    ufo = ufoLib2.Font.open(ufo_path)
    if context is not None:
        info = FontInfo.from_context(
            context,
            ufo.info.familyName or "Imported",
            ufo.info.styleName or "Regular",
        )
        font = Font(info=info, context=context)
    else:
        # System/Drawing path: FontInfo alone — no DesignContext required.
        info = FontInfo(
            family_name=ufo.info.familyName or "Imported",
            style_name=ufo.info.styleName or "Regular",
            units_per_em=float(ufo.info.unitsPerEm or 1000),
            ascender=float(ufo.info.ascender or 750),
            descender=float(ufo.info.descender or -200),
            x_height=float(ufo.info.xHeight or 500),
            cap_height=float(ufo.info.capHeight or 700),
        )
        font = Font(info=info)
    for glyph in ufo:
        if not glyph.name:
            continue
        rec = RecordingPen()
        glyph.draw(rec)
        outline = _outline_from_recording(rec)
        font.add_glyph(
            Glyph(
                glyph.name,
                outline,
                float(glyph.width or 0),
                unicodes=tuple(glyph.unicodes),
            ),
            replace=True,
        )
    return font
