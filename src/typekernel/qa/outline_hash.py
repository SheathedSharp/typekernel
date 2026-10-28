"""Stable content hashes of outlines for change detection (not golden gates)."""

from __future__ import annotations

import hashlib

from typekernel.font.glyph import Glyph
from typekernel.geo.outline import Outline

__all__ = ["DEFAULT_NDIGITS", "glyph_hash", "outline_hash"]

DEFAULT_NDIGITS = 3


def _fmt(v: float, ndigits: int) -> str:
    return f"{round(float(v), ndigits):.{ndigits}f}"


def outline_hash(outline: Outline, *, ndigits: int = DEFAULT_NDIGITS) -> str:
    """Hash contour segment coordinates (rounded) for diffing edits."""
    parts: list[str] = []
    for ci, contour in enumerate(outline.contours):
        parts.append(f"c{ci}:{'C' if contour.closed else 'O'}")
        for seg in contour.segments:
            pts = ",".join(
                f"{_fmt(p.x, ndigits)}:{_fmt(p.y, ndigits)}" for p in seg.points
            )
            parts.append(f"{seg.kind}:{pts}")
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest


def glyph_hash(glyph: Glyph, *, ndigits: int = DEFAULT_NDIGITS) -> str:
    """Hash a glyph's outline plus advance (for project diffs)."""
    base = outline_hash(glyph.outline, ndigits=ndigits)
    adv = _fmt(glyph.advance, ndigits)
    return hashlib.sha256(f"{base}|{adv}".encode()).hexdigest()
