"""Before/after smooth joins for ``zayju`` with join close-ups.

Before: previous recipes (union + fillet pads + faceted polyline hook).
After: ``blend_joins`` / ``smooth_hook`` recipes. Both rows are optically
spaced with :func:`typekernel.optics.space.space_word_optical`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from typekernel.geo.joins import SMOOTH_DEG, join_angles
from typekernel.geo.segment import LineSegment
from typekernel.optics.space import space_word_optical
from typekernel.parts import ComposedGlyph, DesignContext, layout_glyphs
from typekernel.parts.latin import word_zayju
from typekernel.qa.score import WordReport, word_report

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
DOCS_IMG = HERE.parents[1] / "docs" / "images"
NAME = "zayju-smooth-joins-before-after.png"
sys.path.insert(0, str(HERE.parents[1] / "examples" / "optical_spacing"))
from design_compare import _bake_otf  # type: ignore[import-not-found]

BG = (255, 255, 255)
FG = (22, 22, 26)
SUB = (110, 110, 120)
RED = (220, 50, 47)
BLUE = (38, 110, 220)
LABEL_FONT = "/System/Library/Fonts/SFNS.ttf"


def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(LABEL_FONT, size=size)
    except OSError:
        return ImageFont.load_default()


def _before_glyphs(ctx: DesignContext) -> list[ComposedGlyph]:
    spec = importlib.util.spec_from_file_location("_latin_before", HERE / "_latin_before.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.word_zayju(ctx))


def _word_panel(glyphs, kern, w: int, h: int, xh_px: float) -> Image.Image:
    names = list("zayju")
    ctx = glyphs[0].context
    scale = xh_px / ctx.x_height
    px = max(12, round(ctx.units_per_em * scale))
    ss = 3
    font = ImageFont.truetype(str(_bake_otf(glyphs, names, OUT_DIR / "_tmp")), size=px * ss)
    xs = [x * scale for x in layout_glyphs(glyphs, names, kerning=kern)]
    content = xs[-1] + glyphs[-1].advance * scale
    x0 = (w - content) / 2
    base = h * 0.66
    img = Image.new("RGB", (w * ss, h * ss), BG)
    d = ImageDraw.Draw(img)
    for ch, x in zip(names, xs):
        d.text(((x0 + x) * ss, base * ss), ch, font=font, fill=FG, anchor="ls")
    return img.resize((w, h), Image.Resampling.LANCZOS)


def _sample(seg, n: int = 24) -> list[tuple[float, float]]:
    if isinstance(seg, LineSegment):
        return [seg.p0.as_tuple(), seg.p1.as_tuple()]
    p0, p1, p2, p3 = seg.points
    pts = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        pts.append(
            (
                mt**3 * p0.x + 3 * mt * mt * t * p1.x + 3 * mt * t * t * p2.x + t**3 * p3.x,
                mt**3 * p0.y + 3 * mt * mt * t * p1.y + 3 * mt * t * t * p2.y + t**3 * p3.y,
            )
        )
    return pts


def _closeup(glyph: ComposedGlyph, box: tuple[float, float, float, float], size: int) -> Image.Image:
    """Filled glyph region + outline; red dots mark non-smooth joins."""
    x0, y0, x1, y1 = box
    s = size / max(x1 - x0, y1 - y0)
    ss = 3
    img = Image.new("RGB", (size * ss, size * ss), BG)
    d = ImageDraw.Draw(img)

    def tp(p: tuple[float, float]) -> tuple[float, float]:
        return ((p[0] - x0) * s * ss, (y1 - p[1]) * s * ss)

    # fill via even-odd XOR of contour polygons
    mask = Image.new("1", img.size, 0)
    for o in list(glyph.solids) + list(glyph.holes):
        for c in o.contours:
            poly = [tp(p) for seg in c.segments for p in _sample(seg)]
            layer = Image.new("1", img.size, 0)
            ImageDraw.Draw(layer).polygon(poly, fill=1)
            mask = Image.frombytes("1", img.size, bytes(a ^ b for a, b in zip(mask.tobytes(), layer.tobytes())))
    img.paste(Image.new("RGB", img.size, (205, 205, 212)), mask=mask)
    for o in list(glyph.solids) + list(glyph.holes):
        for c in o.contours:
            for seg in c.segments:
                d.line([tp(p) for p in _sample(seg)], fill=BLUE, width=2 * ss)
            angs = join_angles(c)
            for i, seg in enumerate(c.segments):
                end = seg.p1 if isinstance(seg, LineSegment) else seg.p3
                x, y = tp(end.as_tuple())
                r = 5 * ss
                col = RED if angs[i] >= SMOOTH_DEG else FG
                rr = r if angs[i] >= SMOOTH_DEG else r * 0.5
                d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
    return img.resize((size, size), Image.Resampling.LANCZOS)


def _row_label(rep: WordReport) -> str:
    return (
        f"G1 breaks {rep.g1_join_error_count}/{rep.g1_join_total}  ·  kinks {rep.kink_count}  ·  "
        f"corners {rep.corner_count}  ·  flat terminals {rep.terminal_count}  ·  "
        f"optical ratio {rep.optical_gap_ratio:.2f}  ·  stem CV {rep.stem_cv:.3f}"
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ctx = DesignContext.geometric_sans()
    names = list("zayju")
    rows = []
    for title, glyphs in (
        ("Before — union + fillet pads, faceted hook", _before_glyphs(ctx)),
        ("After — blended joins, continuous hook", word_zayju(ctx)),
    ):
        sp = space_word_optical(glyphs, names)
        rep = word_report(list(sp.glyphs), names, kerning=sp.kerning)
        rep.write_json(OUT_DIR / f"{'before' if title.startswith('Before') else 'after'}.json")
        rows.append((title, list(sp.glyphs), sp.kerning, rep))

    word_w, row_h, cu = 860, 300, 300
    margin, gap = 28, 16
    head = 70
    total_w = margin * 2 + word_w + 3 * (cu + gap)
    total_h = margin * 2 + 2 * (head + row_h) + gap
    canvas = Image.new("RGB", (total_w, total_h), BG)
    d = ImageDraw.Draw(canvas)
    tf, sf, cf = _font(24), _font(14), _font(13)
    xh = ctx.x_height
    t = ctx.stem
    # close-up windows in glyph-local coords (after sidebearing packing)
    crops = {
        "a": lambda g: (g, "a · stem-to-bowl"),
        "y": lambda g: (g, "y · crotch"),
        "j": lambda g: (g, "j · hook"),
    }
    for r, (title, glyphs, kern, rep) in enumerate(rows):
        y = margin + r * (head + row_h + gap)
        d.text((margin, y), title, font=tf, fill=FG)
        d.text((margin, y + 34), _row_label(rep), font=sf, fill=SUB)
        canvas.paste(_word_panel(glyphs, kern, word_w, row_h, 110.0), (margin, y + head))
        by_name = dict(zip(names, glyphs))
        windows = {
            "a": (by_name["a"], None),
            "y": (by_name["y"], None),
            "j": (by_name["j"], None),
        }
        for i, ch in enumerate(("a", "y", "j")):
            g = windows[ch][0]
            from typekernel.geo.layout import union_bounds

            bx = union_bounds(list(g.solids) + list(g.holes))
            if ch == "a":
                cxw = bx[2] - t
                win = (cxw - xh * 0.3, xh * 0.45, cxw + xh * 0.3, xh * 1.05)
            elif ch == "y":
                mid = (bx[0] + bx[2]) / 2
                win = (mid - xh * 0.38, -xh * 0.25, mid + xh * 0.38, xh * 0.51)
            else:
                win = (bx[0] - t * 0.2, ctx.descender - t * 0.3, bx[2] + t * 0.2, ctx.descender - t * 0.3 + (bx[2] - bx[0] + t * 0.4))
            x = margin + word_w + gap + i * (cu + gap)
            canvas.paste(_closeup(g, win, cu), (x, y + head))
            d.rectangle([x, y + head, x + cu - 1, y + head + cu - 1], outline=(220, 220, 224))
            d.text((x + 8, y + head + 6), crops[ch](g)[1], font=cf, fill=SUB)
    d.text(
        (margin, total_h - margin + 4),
        "close-ups: blue outline · red dot = G1 break · small black dot = smooth join",
        font=cf,
        fill=SUB,
    )
    out = OUT_DIR / "compare.png"
    canvas.save(out, optimize=True)
    canvas.save(DOCS_IMG / NAME, optimize=True)
    for title, _, _, rep in rows:
        print(title, rep.to_dict())
    print("wrote", out, DOCS_IMG / NAME)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
