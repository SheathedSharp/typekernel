"""Hook for checking that masters can interpolate.

Full glyphset / UFO checks belong to ``fontTools.varLib.interpolatable``.
This module only offers a lightweight topology pass over kernel
:class:`~typekernel.geo.outline.Outline` values so callers can fail fast
before writing a designspace.
"""

from __future__ import annotations

from collections.abc import Sequence

from typekernel.geo.outline import Outline


def check_interpolatable(outlines: Sequence[Outline]) -> list[str]:
    """Return human-readable topology problems, or an empty list if compatible.

    v0 compares contour counts and per-segment kinds across the sequence.
    It does not call ``fontTools.varLib.interpolatable`` (that API expects
    fontTools glyphsets / UFOs). Use that library for production glyphset
    audits: ``fontTools.varLib.interpolatable``.
    """
    if len(outlines) < 2:
        return []

    problems: list[str] = []
    reference = outlines[0]
    for index, outline in enumerate(outlines[1:], start=1):
        if outline.contour_count != reference.contour_count:
            problems.append(
                f"outline[{index}]: contour count {outline.contour_count} "
                f"!= reference {reference.contour_count}"
            )
            continue
        for contour_index, (ref_contour, other_contour) in enumerate(
            zip(reference.contours, outline.contours, strict=True)
        ):
            if len(ref_contour.segments) != len(other_contour.segments):
                problems.append(
                    f"outline[{index}] contour[{contour_index}]: segment count "
                    f"{len(other_contour.segments)} != reference "
                    f"{len(ref_contour.segments)}"
                )
                continue
            for segment_index, (ref_seg, other_seg) in enumerate(
                zip(ref_contour.segments, other_contour.segments, strict=True)
            ):
                if ref_seg.kind != other_seg.kind:
                    problems.append(
                        f"outline[{index}] contour[{contour_index}] "
                        f"segment[{segment_index}]: kind {other_seg.kind!r} "
                        f"!= reference {ref_seg.kind!r}"
                    )
    return problems
