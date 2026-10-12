"""Optional boolean operations, delegated to skia-pathops.

Boolean geometry is **not** implemented with Shapely. Shapely operates on
polygons, so using it would mean turning cubic outlines into polygons first —
exactly the lossy flattening this kernel forbids as a design truth.
``skia-pathops`` works on real curves, so it is the only acceptable backend, and
it stays behind an optional extra rather than becoming a hard dependency.

When ``skia-pathops`` is installed, :func:`boolean_op` converts cubic
:class:`~typekernel.geo.outline.Outline` values to pathops paths, runs the
operation, and rebuilds cubic outlines from the result (quadratic pieces from
pathops, if any, are elevated to cubics).
"""

from __future__ import annotations

from typing import Literal

from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

BooleanOp = Literal["union", "intersection", "difference"]
"""The boolean operations this module supports."""

BOOLEAN_OPS: frozenset[str] = frozenset({"union", "intersection", "difference"})

INSTALL_HINT = (
    "boolean operations require the optional extra: "
    'pip install "typekernel[boolean]"'
)

_OP_NAME = {
    "union": "UNION",
    "intersection": "INTERSECTION",
    "difference": "DIFFERENCE",
}


def boolean_op(a: Outline, b: Outline, op: BooleanOp) -> Outline:
    """Combine two outlines with a boolean operation via skia-pathops.

    Raises:
        ValueError: if ``op`` is not a known operation.
        RuntimeError: if ``skia-pathops`` is not installed, with the install
            hint for the ``boolean`` extra.
    """
    if op not in BOOLEAN_OPS:
        raise ValueError(
            f"unknown boolean op {op!r}; expected one of {sorted(BOOLEAN_OPS)}"
        )

    try:
        import pathops
        from pathops import Path, PathOp
    except ImportError as exc:
        raise RuntimeError(INSTALL_HINT) from exc

    path_a = _outline_to_path(a, Path)
    path_b = _outline_to_path(b, Path)
    builder = pathops.OpBuilder(fix_winding=True)
    if op == "union":
        builder.add(path_a, PathOp.UNION)
        builder.add(path_b, PathOp.UNION)
    else:
        # Subject first, then operand with the requested op.
        builder.add(path_a, PathOp.UNION)
        builder.add(path_b, getattr(PathOp, _OP_NAME[op]))
    return _path_to_outline(builder.resolve())


def union_all(outlines: list[Outline]) -> Outline:
    """Union many outlines into one (requires ``typekernel[boolean]``).

    An empty list raises ``ValueError``. A single outline is returned unchanged.
    """
    if not outlines:
        raise ValueError("union_all requires at least one outline")
    if len(outlines) == 1:
        return outlines[0]
    try:
        import pathops
        from pathops import Path, PathOp
    except ImportError as exc:
        raise RuntimeError(INSTALL_HINT) from exc

    builder = pathops.OpBuilder(fix_winding=True)
    for outline in outlines:
        builder.add(_outline_to_path(outline, Path), PathOp.UNION)
    return _path_to_outline(builder.resolve())


def _outline_to_path(outline: Outline, path_cls: type) -> object:
    path = path_cls()
    for contour in outline.contours:
        if not contour.segments:
            continue
        start = contour.segments[0].points[0]
        path.moveTo(start.x, start.y)
        for segment in contour.segments:
            if isinstance(segment, CubicSegment):
                path.cubicTo(
                    segment.p1.x,
                    segment.p1.y,
                    segment.p2.x,
                    segment.p2.y,
                    segment.p3.x,
                    segment.p3.y,
                )
            else:
                path.lineTo(segment.p1.x, segment.p1.y)
        if contour.closed:
            path.close()
    return path


def _path_to_outline(path: object) -> Outline:
    from fontTools.pens.recordingPen import RecordingPen

    rec = RecordingPen()
    path.draw(rec)  # type: ignore[attr-defined]

    contours: list[Contour] = []
    segments: list[LineSegment | CubicSegment] = []
    current: Point | None = None
    start: Point | None = None

    def flush(*, closed: bool) -> None:
        nonlocal segments, current, start
        if segments:
            contours.append(Contour(tuple(segments), closed=closed))
        segments = []
        current = None
        start = None

    for op, args in rec.value:
        if op == "moveTo":
            if segments:
                flush(closed=False)
            pt = Point(float(args[0][0]), float(args[0][1]))
            current = start = pt
        elif op == "lineTo":
            if current is None:
                raise RuntimeError("lineTo without moveTo in pathops output")
            end = Point(float(args[0][0]), float(args[0][1]))
            segments.append(LineSegment(current, end))
            current = end
        elif op == "curveTo":
            if current is None:
                raise RuntimeError("curveTo without moveTo in pathops output")
            if len(args) == 3:
                c1 = Point(float(args[0][0]), float(args[0][1]))
                c2 = Point(float(args[1][0]), float(args[1][1]))
                end = Point(float(args[2][0]), float(args[2][1]))
                segments.append(CubicSegment(current, c1, c2, end))
                current = end
            elif len(args) == 2:
                q1 = Point(float(args[0][0]), float(args[0][1]))
                end = Point(float(args[1][0]), float(args[1][1]))
                c1 = Point(
                    current.x + 2.0 / 3.0 * (q1.x - current.x),
                    current.y + 2.0 / 3.0 * (q1.y - current.y),
                )
                c2 = Point(
                    end.x + 2.0 / 3.0 * (q1.x - end.x),
                    end.y + 2.0 / 3.0 * (q1.y - end.y),
                )
                segments.append(CubicSegment(current, c1, c2, end))
                current = end
            else:
                raise RuntimeError(f"unexpected curveTo arity: {len(args)}")
        elif op == "qCurveTo":
            if current is None:
                raise RuntimeError("qCurveTo without moveTo in pathops output")
            pts = [Point(float(p[0]), float(p[1])) for p in args]
            if len(pts) == 1:
                end = pts[0]
                segments.append(LineSegment(current, end))
                current = end
            else:
                on = pts[-1]
                offs = pts[:-1]
                cursor = current
                for i, off in enumerate(offs):
                    if i < len(offs) - 1:
                        end_pt = Point(
                            (off.x + offs[i + 1].x) / 2.0,
                            (off.y + offs[i + 1].y) / 2.0,
                        )
                    else:
                        end_pt = on
                    c1 = Point(
                        cursor.x + 2.0 / 3.0 * (off.x - cursor.x),
                        cursor.y + 2.0 / 3.0 * (off.y - cursor.y),
                    )
                    c2 = Point(
                        end_pt.x + 2.0 / 3.0 * (off.x - end_pt.x),
                        end_pt.y + 2.0 / 3.0 * (off.y - end_pt.y),
                    )
                    segments.append(CubicSegment(cursor, c1, c2, end_pt))
                    cursor = end_pt
                current = cursor
        elif op == "closePath":
            if current is not None and start is not None and current != start:
                segments.append(LineSegment(current, start))
                current = start
            flush(closed=True)
        elif op == "endPath":
            flush(closed=False)
        else:
            raise RuntimeError(f"unsupported pen op from pathops: {op!r}")

    if segments:
        flush(closed=False)
    return Outline(tuple(contours))
