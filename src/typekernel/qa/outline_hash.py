"""Stable hash of an outline's quantized coordinates for regression checks.

The digest is derived only from contour structure and coordinates — never from
Python object ids, insertion order of dicts with random salts, or wall-clock
time. The same geometry always hashes the same way.
"""

from __future__ import annotations

import hashlib

from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.rounding import DEFAULT_NDIGITS, quantize
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.parts.compose import ComposedGlyph


def outline_hash(outline: Outline, *, ndigits: int = DEFAULT_NDIGITS) -> str:
    """Return a hex SHA-256 of the outline's canonical quantized form.

    Coordinates are quantized with :func:`~typekernel.geo.rounding.quantize`
    (default three decimal places) before hashing so tiny float noise does not
    thrash the digest while a real point move still changes it.

    Args:
        outline: The outline to hash.
        ndigits: Decimal places for quantization (same rule as ``quantize``).

    Returns:
        Lowercase hex SHA-256 digest string.
    """
    canonical = _canonical_text(outline, ndigits=ndigits)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def composed_glyph_hash(glyph: ComposedGlyph, *, ndigits: int = DEFAULT_NDIGITS) -> str:
    """Hash all solid and hole contours of a composed glyph as one outline."""
    contours = tuple(
        contour for outline in (*glyph.solids, *glyph.holes) for contour in outline.contours
    )
    return outline_hash(Outline(contours), ndigits=ndigits)


def _canonical_text(outline: Outline, *, ndigits: int) -> str:
    """Serialize contours to a stable, line-oriented text form."""
    lines: list[str] = [f"contours={len(outline.contours)}"]
    for contour_index, contour in enumerate(outline.contours):
        closed_flag = "1" if contour.closed else "0"
        lines.append(f"c{contour_index} closed={closed_flag} n={len(contour.segments)}")
        for segment_index, segment in enumerate(contour.segments):
            if isinstance(segment, LineSegment):
                coords = _fmt_points(segment.points, ndigits=ndigits)
                lines.append(f"c{contour_index}s{segment_index} line {coords}")
            elif isinstance(segment, CubicSegment):
                coords = _fmt_points(segment.points, ndigits=ndigits)
                lines.append(f"c{contour_index}s{segment_index} cubic {coords}")
            else:  # pragma: no cover - Contour typing forbids other kinds
                raise TypeError(f"unsupported segment type: {type(segment)!r}")
    return "\n".join(lines) + "\n"


def _fmt_points(points: tuple[Point, ...], *, ndigits: int) -> str:
    parts: list[str] = []
    for point in points:
        x = quantize(point.x, ndigits)
        y = quantize(point.y, ndigits)
        parts.append(f"{x:.{ndigits}f},{y:.{ndigits}f}")
    return " ".join(parts)
