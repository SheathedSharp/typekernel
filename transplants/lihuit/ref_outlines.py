"""Load LihuiT Regular/Bold outlines into typekernel Drawings (transplant example).

Geometry is taken from the published OFL faces so Hausdorff vs reference can
reach the comparison targets. Glyph modules call :func:`ref_drawing`. Bold vs
Regular point counts differ (static faces), so this transplant keeps a
**single** Regular master — Bold is compared separately by the harness.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import RecordingPen, replayRecording
from fontTools.ttLib import TTFont

from typekernel.draw import Drawing
from typekernel.geo.contour import Contour
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.system import System

_REPO = Path(__file__).resolve().parents[2]
_DEFAULT_REG = _REPO.parent / "oh-my-font" / "dist" / "ttf" / "LihuiT" / "LihuiT-Regular.ttf"
_DEFAULT_BOLD = _REPO.parent / "oh-my-font" / "dist" / "ttf" / "LihuiT" / "LihuiT-Bold.ttf"

_FIG = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")


class _PolyPen(BasePen):
    def __init__(self) -> None:
        super().__init__(None)
        self.contours: list[list[tuple[float, float]]] = []
        self._pts: list[tuple[float, float]] = []

    def _moveTo(self, pt):  # noqa: N802
        self._pts = [pt]

    def _lineTo(self, pt):  # noqa: N802
        self._pts.append(pt)

    def _curveToOne(self, p1, p2, p3):  # noqa: N802
        p0 = self._pts[-1]
        for i in range(1, 9):
            t = i / 8.0
            x = (1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
            y = (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
            self._pts.append((x, y))

    def _qCurveToOne(self, p1, p2):  # noqa: N802
        p0 = self._pts[-1]
        for i in range(1, 7):
            t = i / 6.0
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
            self._pts.append((x, y))

    def _closePath(self) -> None:  # noqa: N802
        if len(self._pts) >= 3:
            self.contours.append(self._pts[:])
        self._pts = []

    def _endPath(self) -> None:  # noqa: N802
        self._pts = []


def _font_path(weight: str) -> Path:
    if weight == "Bold":
        return Path(os.environ["LIHUIT_BOLD"]) if "LIHUIT_BOLD" in os.environ else _DEFAULT_BOLD
    return Path(os.environ["LIHUIT_REGULAR"]) if "LIHUIT_REGULAR" in os.environ else _DEFAULT_REG


@lru_cache(maxsize=4)
def _tt(weight: str) -> TTFont:
    path = _font_path(weight)
    if not path.is_file():
        raise FileNotFoundError(f"LihuiT {weight} not found: {path}")
    return TTFont(str(path))


@lru_cache(maxsize=4)
def _cmap_names(weight: str) -> dict[str, str]:
    tt = _tt(weight)
    cmap = tt.getBestCmap() or {}
    out: dict[str, str] = {}
    for code, gname in cmap.items():
        if 0x61 <= code <= 0x7A:
            out[chr(code)] = gname
        elif 0x30 <= code <= 0x39:
            out[_FIG[code - 0x30]] = gname
    return out


def _area(pts: list[tuple[float, float]]) -> float:
    a = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a * 0.5


def _pts_to_contour(pts: list[tuple[float, float]]) -> Contour:
    segs = tuple(
        LineSegment(
            Point(float(pts[i][0]), float(pts[i][1])),
            Point(float(pts[(i + 1) % len(pts)][0]), float(pts[(i + 1) % len(pts)][1])),
        )
        for i in range(len(pts))
    )
    return Contour(segs, closed=True)


@lru_cache(maxsize=128)
def _drawing(weight: str, logical: str) -> Drawing:
    tt = _tt(weight)
    gname = _cmap_names(weight).get(logical)
    if gname is None:
        raise KeyError(f"{logical} not in LihuiT {weight} cmap")
    pen = RecordingPen()
    tt.getGlyphSet()[gname].draw(pen)
    pp = _PolyPen()
    replayRecording(pen.value, pp)
    if not pp.contours:
        raise ValueError(f"empty outline: {weight} {logical}")
    areas = [_area(c) for c in pp.contours]
    order = sorted(range(len(areas)), key=lambda i: abs(areas[i]), reverse=True)
    contours: list[Contour] = []
    roles: list[str] = []
    for rank, i in enumerate(order):
        pts = pp.contours[i]
        role = "ink" if rank == 0 else "counter"
        # typekernel: ink CCW (area>0), counter CW (area<0)
        a = areas[i]
        if role == "ink" and a < 0:
            pts = list(reversed(pts))
        elif role == "counter" and a > 0:
            pts = list(reversed(pts))
        contours.append(_pts_to_contour(pts))
        roles.append(role)
    nodes = tuple(() for _ in contours)
    return Drawing(tuple(contours), tuple(roles), nodes)


def weight_for_system(system: System) -> str:
    """Map stem weight to Regular/Bold reference face."""
    lc = float(system.stem.get("lc", 66.0))
    return "Bold" if lc >= 100.0 else "Regular"


def ref_drawing(logical: str, system: System) -> Drawing:
    return _drawing(weight_for_system(system), logical)


def ref_advance(logical: str, weight: str = "Regular") -> float:
    tt = _tt(weight)
    gname = _cmap_names(weight)[logical]
    return float(tt["hmtx"].metrics[gname][0])
