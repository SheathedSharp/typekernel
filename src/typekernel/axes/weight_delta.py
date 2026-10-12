"""Weight as designed point/handle deltas between masters.

``WeightDelta`` stores per-point ``(dx, dy)`` offsets derived from a Regular /
Bold (or any two compatible) outline pair. Applying a scalar ``t`` moves every
point and handle along those deltas.

This is deliberately **not** a stroke radius, buffer width, or pen expansion.
A single float “stem width” is not a weight model in this package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

SegmentKind = Literal["line", "cubic"]
PointDelta = tuple[float, float]
SegmentDeltas = tuple[PointDelta, ...]
ContourDeltas = tuple[SegmentDeltas, ...]


@dataclass(frozen=True, slots=True)
class WeightDelta:
    """Point/handle deltas between two topologically compatible outlines.

    Attributes:
        deltas: Nested ``(dx, dy)`` tuples mirroring outline → contour →
            segment → point order. Line segments hold two deltas; cubics hold
            four (including off-curve handles).
        kinds: Segment kind (``"line"`` / ``"cubic"``) per contour, same shape
            as ``deltas``, used to validate ``apply`` targets.
    """

    deltas: tuple[ContourDeltas, ...]
    kinds: tuple[tuple[SegmentKind, ...], ...]

    @classmethod
    def from_masters(cls, regular: Outline, bold: Outline) -> WeightDelta:
        """Build deltas as ``bold − regular`` for every point and handle.

        Raises:
            ValueError: if contour counts differ, or any corresponding segments
                differ in kind (topology mismatch).
        """
        if regular.contour_count != bold.contour_count:
            raise ValueError(
                "master outlines have different contour counts: "
                f"{regular.contour_count} vs {bold.contour_count}"
            )

        all_deltas: list[ContourDeltas] = []
        all_kinds: list[tuple[SegmentKind, ...]] = []

        for contour_index, (reg_contour, bold_contour) in enumerate(
            zip(regular.contours, bold.contours, strict=True)
        ):
            if len(reg_contour.segments) != len(bold_contour.segments):
                raise ValueError(
                    f"contour {contour_index}: segment count mismatch "
                    f"({len(reg_contour.segments)} vs {len(bold_contour.segments)})"
                )

            contour_deltas: list[SegmentDeltas] = []
            contour_kinds: list[SegmentKind] = []

            for segment_index, (reg_seg, bold_seg) in enumerate(
                zip(reg_contour.segments, bold_contour.segments, strict=True)
            ):
                if reg_seg.kind != bold_seg.kind:
                    raise ValueError(
                        f"contour {contour_index} segment {segment_index}: "
                        f"kind mismatch ({reg_seg.kind!r} vs {bold_seg.kind!r})"
                    )
                point_deltas = tuple(
                    (bold_pt.x - reg_pt.x, bold_pt.y - reg_pt.y)
                    for reg_pt, bold_pt in zip(reg_seg.points, bold_seg.points, strict=True)
                )
                contour_deltas.append(point_deltas)
                contour_kinds.append(reg_seg.kind)

            all_deltas.append(tuple(contour_deltas))
            all_kinds.append(tuple(contour_kinds))

        return cls(deltas=tuple(all_deltas), kinds=tuple(all_kinds))

    def apply(self, outline: Outline, t: float) -> Outline:
        """Return ``outline`` with every point moved by ``t * delta``.

        ``t=0`` is identity; ``t=1`` reaches the bold master when ``outline``
        was the regular master used in :meth:`from_masters`.

        Raises:
            ValueError: if ``outline`` does not match the stored topology.
        """
        _assert_compatible(outline, self.kinds)

        new_contours: list[Contour] = []
        for contour, contour_deltas in zip(outline.contours, self.deltas, strict=True):
            new_segments: list[LineSegment | CubicSegment] = []
            for segment, point_deltas in zip(contour.segments, contour_deltas, strict=True):
                moved = tuple(
                    Point(point.x + t * dx, point.y + t * dy)
                    for point, (dx, dy) in zip(segment.points, point_deltas, strict=True)
                )
                if segment.kind == "line":
                    new_segments.append(LineSegment(moved[0], moved[1]))
                else:
                    new_segments.append(CubicSegment(moved[0], moved[1], moved[2], moved[3]))
            new_contours.append(Contour(tuple(new_segments), closed=contour.closed))
        return Outline(tuple(new_contours))


def _assert_compatible(outline: Outline, kinds: tuple[tuple[SegmentKind, ...], ...]) -> None:
    if outline.contour_count != len(kinds):
        raise ValueError(
            "outline contour count does not match WeightDelta topology: "
            f"{outline.contour_count} vs {len(kinds)}"
        )
    for contour_index, (contour, contour_kinds) in enumerate(
        zip(outline.contours, kinds, strict=True)
    ):
        if len(contour.segments) != len(contour_kinds):
            raise ValueError(
                f"contour {contour_index}: segment count does not match "
                f"WeightDelta ({len(contour.segments)} vs {len(contour_kinds)})"
            )
        for segment_index, (segment, kind) in enumerate(
            zip(contour.segments, contour_kinds, strict=True)
        ):
            if segment.kind != kind:
                raise ValueError(
                    f"contour {contour_index} segment {segment_index}: "
                    f"kind mismatch ({segment.kind!r} vs {kind!r})"
                )
