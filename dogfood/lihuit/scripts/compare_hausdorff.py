"""P6-3: compare dogfood outlines to LihuiT Regular/Bold (symmetric Hausdorff)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
DEFAULT_REG = REPO.parent / "oh-my-font" / "dist" / "ttf" / "LihuiT" / "LihuiT-Regular.ttf"
DEFAULT_BOLD = REPO.parent / "oh-my-font" / "dist" / "ttf" / "LihuiT" / "LihuiT-Bold.ttf"

# lc + figs only for the transplant scope
GLYPHS = list("abcdefghijklmnopqrstuvwxyz") + [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"
]


def _font_path(env: str, default: Path) -> Path:
    raw = os.environ.get(env)
    return Path(raw) if raw else default


def _outline_points(tt, name: str, *, n: int = 64) -> list[tuple[float, float]]:
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.pens.recordingPen import replayRecording
    from fontTools.pens.basePen import BasePen

    glyph_set = tt.getGlyphSet()
    if name not in glyph_set:
        # try cmap name via best effort unicodes for a-z / 0-9
        return []
    pen = RecordingPen()
    glyph_set[name].draw(pen)

    pts: list[tuple[float, float]] = []

    class SamplePen(BasePen):
        def __init__(self):
            super().__init__(None)
            self.pts = []

        def _moveTo(self, pt):
            self.pts.append(pt)

        def _lineTo(self, pt):
            self.pts.append(pt)

        def _curveToOne(self, p1, p2, p3):
            # coarse sample
            for i in range(1, 5):
                t = i / 4.0
                # de Casteljau-ish linear blend (good enough for distance proxy)
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


def main() -> int:
    from fontTools.ttLib import TTFont

    from typekernel.project import open_project

    reg_path = _font_path("LIHUIT_REGULAR", DEFAULT_REG)
    bold_path = _font_path("LIHUIT_BOLD", DEFAULT_BOLD)
    if not reg_path.is_file():
        print(f"missing reference Regular: {reg_path}", file=sys.stderr)
        return 2

    ref = TTFont(str(reg_path))
    # Map a-z / 0-9 via cmap
    cmap = ref.getBestCmap() or {}
    code_to_name = {}
    for code, gname in cmap.items():
        if 0x61 <= code <= 0x7A:  # a-z
            code_to_name[chr(code)] = gname
        if 0x30 <= code <= 0x39:
            code_to_name[
                ["zero","one","two","three","four","five","six","seven","eight","nine"][code - 0x30]
            ] = gname

    distances: list[tuple[str, float]] = []
    missing: list[str] = []
    with open_project(ROOT) as session:
        for name in GLYPHS:
            if name not in session.specs():
                missing.append(name)
                continue
            ref_name = code_to_name.get(name)
            if not ref_name:
                missing.append(name)
                continue
            # dogfood outline via evaluated drawing → sample contour points
            drawing = session.evaluate(name).drawing
            ours: list[tuple[float, float]] = []
            for c in drawing.outline().contours:
                for seg in c.segments:
                    for pt in seg.points:
                        ours.append((float(pt.x), float(pt.y)))
            theirs = _outline_points(ref, ref_name)
            d = _hausdorff(ours, theirs)
            distances.append((name, d))

    distances.sort(key=lambda x: x[1], reverse=True)
    finite = [d for _, d in distances if d != float("inf")]
    print(f"compared={len(finite)} missing={missing[:12]}{'...' if len(missing)>12 else ''}")
    if not finite:
        print("no finite distances — check glyph presence / cmap")
        return 1
    finite_sorted = sorted(finite)
    n = len(finite_sorted)
    median = finite_sorted[n // 2]
    p95 = finite_sorted[min(n - 1, int(n * 0.95))]
    print(f"median={median:.2f} p95={p95:.2f} (targets ≤8 / ≤20)")
    print("worst 10:")
    for name, d in distances[:10]:
        print(f"  {name:10s} {d:.2f}")
    # Bold path noted for later dual-master compare
    print(f"bold_ref={'ok' if bold_path.is_file() else 'missing'}: {bold_path}")
    return 0 if median <= 8 and p95 <= 20 else 1


if __name__ == "__main__":
    raise SystemExit(main())
