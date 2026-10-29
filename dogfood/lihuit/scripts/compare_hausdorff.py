"""P6-3: compare dogfood outlines to LihuiT Regular/Bold (symmetric Hausdorff)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
DEFAULT_REG = REPO.parent / "oh-my-font" / "dist" / "ttf" / "LihuiT" / "LihuiT-Regular.ttf"
DEFAULT_BOLD = REPO.parent / "oh-my-font" / "dist" / "ttf" / "LihuiT" / "LihuiT-Bold.ttf"

GLYPHS = list("abcdefghijklmnopqrstuvwxyz") + [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"
]


def _font_path(env: str, default: Path) -> Path:
    raw = os.environ.get(env)
    return Path(raw) if raw else default


def _outline_points(tt, name: str) -> list[tuple[float, float]]:
    from fontTools.pens.basePen import BasePen
    from fontTools.pens.recordingPen import RecordingPen, replayRecording

    glyph_set = tt.getGlyphSet()
    if name not in glyph_set:
        return []
    pen = RecordingPen()
    glyph_set[name].draw(pen)

    class SamplePen(BasePen):
        def __init__(self):
            super().__init__(None)
            self.pts = []

        def _moveTo(self, pt):
            self.pts.append(pt)

        def _lineTo(self, pt):
            self.pts.append(pt)

        def _curveToOne(self, p1, p2, p3):
            for i in range(1, 5):
                t = i / 4.0
                x = (1 - t) ** 3 * self._p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t**2 * p2[0] + t**3 * p3[0]
                y = (1 - t) ** 3 * self._p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t**2 * p2[1] + t**3 * p3[1]
                self.pts.append((x, y))
            self._p0 = p3

        def _qCurveToOne(self, p1, p2):
            for i in range(1, 4):
                t = i / 3.0
                x = (1 - t) ** 2 * self._p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
                y = (1 - t) ** 2 * self._p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
                self.pts.append((x, y))
            self._p0 = p2

        def _closePath(self):
            pass

        def _endPath(self):
            pass

        def moveTo(self, pt):
            self._p0 = pt
            super().moveTo(pt)

    sp = SamplePen()
    replayRecording(pen.value, sp)
    return list(sp.pts)


def _hausdorff(a: list[tuple[float, float]], b: list[tuple[float, float]]) -> float:
    if not a or not b:
        return float("inf")

    def directed(src, dst):
        worst = 0.0
        for x, y in src:
            best = min((x - u) ** 2 + (y - v) ** 2 for u, v in dst) ** 0.5
            if best > worst:
                worst = best
        return worst

    return max(directed(a, b), directed(b, a))


def _summarize(distances: list[tuple[str, float]]) -> tuple[float, float]:
    finite = sorted(d for _, d in distances if d != float("inf"))
    n = len(finite)
    if not n:
        return float("inf"), float("inf")
    return finite[n // 2], finite[min(n - 1, int(n * 0.95))]


def _compare_face(label: str, tt_path: Path, *, bold: bool) -> int:
    from fontTools.ttLib import TTFont

    from typekernel.project import open_project

    if not tt_path.is_file():
        print(f"{label}: missing {tt_path}", file=sys.stderr)
        return 2

    ref = TTFont(str(tt_path))
    cmap = ref.getBestCmap() or {}
    code_to_name = {}
    for code, gname in cmap.items():
        if 0x61 <= code <= 0x7A:
            code_to_name[chr(code)] = gname
        if 0x30 <= code <= 0x39:
            code_to_name[
                ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"][code - 0x30]
            ] = gname

    distances: list[tuple[str, float]] = []
    missing: list[str] = []
    with open_project(ROOT) as session:
        # Bold outlines via stem threshold in ref_outlines.weight_for_system
        master = None
        if bold:
            # Evaluate with a Bold-stem system without registering a VF master.
            from system import system as base_sys

            bold_sys = base_sys.tuned(stem={"lc": 116, "lc_h": 100, "uc": 116, "uc_h": 100})
            for name in GLYPHS:
                if name not in session.specs() or name not in code_to_name:
                    missing.append(name)
                    continue
                from ref_outlines import ref_drawing

                drawing = ref_drawing(name, bold_sys)
                ours = []
                for c in drawing.outline().contours:
                    for seg in c.segments:
                        for pt in seg.points:
                            ours.append((float(pt.x), float(pt.y)))
                theirs = _outline_points(ref, code_to_name[name])
                distances.append((name, _hausdorff(ours, theirs)))
        else:
            for name in GLYPHS:
                if name not in session.specs() or name not in code_to_name:
                    missing.append(name)
                    continue
                drawing = session.evaluate(name).drawing
                ours = []
                for c in drawing.outline().contours:
                    for seg in c.segments:
                        for pt in seg.points:
                            ours.append((float(pt.x), float(pt.y)))
                theirs = _outline_points(ref, code_to_name[name])
                distances.append((name, _hausdorff(ours, theirs)))

    distances.sort(key=lambda x: x[1], reverse=True)
    median, p95 = _summarize(distances)
    print(f"=== {label} compared={len(distances)} missing={missing[:8]}")
    print(f"median={median:.2f} p95={p95:.2f} (targets ≤8 / ≤20)")
    print("worst 5:")
    for name, d in distances[:5]:
        print(f"  {name:10s} {d:.2f}")
    return 0 if median <= 8 and p95 <= 20 else 1


def main() -> int:
    reg = _font_path("LIHUIT_REGULAR", DEFAULT_REG)
    bold = _font_path("LIHUIT_BOLD", DEFAULT_BOLD)
    rc = _compare_face("Regular", reg, bold=False)
    rc = max(rc, _compare_face("Bold", bold, bold=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
