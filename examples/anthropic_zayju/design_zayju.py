"""用 typekernel 二创「zayju」，并与苹果系统字、Anthropic Sans 三栏对比。

气质：几何新无衬线——字干匀、开口偏开、终端平切。
灵感来自 Anthropic Sans，二创而非描摹；不参考 zayJu。

运行::

    pip install -e ".[specimen]" && pip install brotli
    python examples/anthropic_zayju/design_zayju.py

中间栏临时下载官网 Anthropic Sans（专有，只本地对比；字体进 /tmp，不入库）。
"""

from __future__ import annotations

import math
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from typekernel.geo import Outline, PathBuilder
from typekernel.geo.contour import Contour
from typekernel.geo.outline import bounds
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

X_HEIGHT = 540.0
STEM = 78.0
OVERSHOOT = 12.0
DESCENDER = -225.0
K = 0.5522847498
SIDE = 56.0

OUT_DIR = Path(__file__).resolve().parent / "out"
DOCS_IMG = Path(__file__).resolve().parents[2] / "docs" / "images"
COMPARE_NAME = "zayju-apple-anthropic-typekernel.png"
ANTHROPIC_SANS_WOFF2 = (
    "https://cdn.prod.website-files.com/67ce28cfec624e2b733f8a52/"
    "69971a00a3295036497e1a28_AnthropicSans-Roman-Web.woff2"
)
APPLE_FONT = "/System/Library/Fonts/SFNS.ttf"
LABEL_FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"

BG = (255, 255, 255, 255)
FG = (24, 24, 28, 255)
LABEL_FG = (50, 50, 58, 255)
SUB_FG = (130, 130, 140, 255)
RULE = (220, 220, 224, 255)


@dataclass(frozen=True)
class Glyph:
    outers: tuple[Outline, ...]
    holes: tuple[Outline, ...]
    advance: float


def translate_outline(outline: Outline, dx: float, dy: float = 0.0) -> Outline:
    def tp(p: Point) -> Point:
        return Point(p.x + dx, p.y + dy)

    contours: list[Contour] = []
    for c in outline.contours:
        segs: list[LineSegment | CubicSegment] = []
        for s in c.segments:
            pts = [tp(p) for p in s.points]
            if isinstance(s, LineSegment):
                segs.append(LineSegment(pts[0], pts[1]))
            else:
                segs.append(CubicSegment(*pts))
        contours.append(Contour(tuple(segs), closed=c.closed))
    return Outline(tuple(contours))


def stroke(pts: list[tuple[float, float]], thickness: float) -> Outline:
    half = thickness / 2.0
    n = len(pts)

    def seg_n(i: int) -> tuple[float, float]:
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        ln = math.hypot(dx, dy) or 1.0
        return (-dy / ln, dx / ln)

    normals = [seg_n(i) for i in range(n - 1)]
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    for i in range(n):
        if i == 0:
            nx, ny = normals[0]
        elif i == n - 1:
            nx, ny = normals[-1]
        else:
            ax, ay = normals[i - 1]
            bx, by = normals[i]
            sx, sy = ax + bx, ay + by
            sl = math.hypot(sx, sy)
            if sl < 1e-6:
                nx, ny = ax, ay
            else:
                nx, ny = sx / sl, sy / sl
                dot = max(-1.0, min(1.0, ax * nx + ay * ny))
                m = min(1.0 / max(dot, 0.45), 2.0)
                nx, ny = nx * m, ny * m
        left.append((pts[i][0] + nx * half, pts[i][1] + ny * half))
        right.append((pts[i][0] - nx * half, pts[i][1] - ny * half))
    b = PathBuilder()
    b.moveTo(*left[0])
    for p in left[1:]:
        b.lineTo(*p)
    b.lineTo(*right[-1])
    for p in reversed(right[:-1]):
        b.lineTo(*p)
    b.closePath()
    return b.build()


def oval(cx: float, cy: float, rx: float, ry: float) -> Outline:
    b = PathBuilder()
    b.moveTo(cx + rx, cy)
    b.curveTo(cx + rx, cy + K * ry, cx + K * rx, cy + ry, cx, cy + ry)
    b.curveTo(cx - K * rx, cy + ry, cx - rx, cy + K * ry, cx - rx, cy)
    b.curveTo(cx - rx, cy - K * ry, cx - K * rx, cy - ry, cx, cy - ry)
    b.curveTo(cx + K * rx, cy - ry, cx + rx, cy - K * ry, cx + rx, cy)
    b.closePath()
    return b.build()


def rect(x0: float, y0: float, x1: float, y1: float) -> Outline:
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    return b.build()


# ---------------------------------------------------------------------------
# Letters
# ---------------------------------------------------------------------------

def design_z() -> Glyph:
    """上下横 + 对角；端点卡在横条上，避免接缝白三角。"""
    t = STEM
    top = X_HEIGHT
    L, R = SIDE, SIDE + 420.0
    # 对角中线：顶横下缘中点偏右 → 底横上缘中点偏左
    # 用「整条 z 中线」stroke，拐角斜接，接缝一体
    cl = [
        (L + t / 2, top - t / 2),
        (R - t / 2, top - t / 2),
        (L + t / 2, t / 2),
        (R - t / 2, t / 2),
    ]
    return Glyph((stroke(cl, t),), (), R + SIDE)


def design_a() -> Glyph:
    """几何单层 a：圆碗 + 右干（Futura / 几何无衬线一路），开口干净。"""
    t = STEM
    top = X_HEIGHT + OVERSHOOT * 0.35
    bot = -OVERSHOOT
    # 外半径按字身高；整字左缘落在 SIDE
    ro = (X_HEIGHT + OVERSHOOT) / 2
    ri = ro - t
    cx = SIDE + ro
    cy = (top + bot) / 2
    outer = oval(cx, cy, ro, ro)
    hole = oval(cx, cy, ri, ri)
    # 右干：贴碗右侧，上探、下到基线
    stem_left = cx + ri * 0.42
    stem_right = stem_left + t
    stem = rect(stem_left, 0.0, stem_right, top + 4)
    advance = max(stem_right, cx + ro) + SIDE
    return Glyph((outer, stem), (hole,), advance)


def design_y() -> Glyph:
    t = STEM
    top = X_HEIGHT
    bot = DESCENDER
    L, R = SIDE, SIDE + 450.0
    jx = (L + R) / 2 - 6
    jy = t * 0.4
    lx, rx = L + t * 0.9, R - t * 0.9
    bx = jx + 48
    left_arm = stroke([(lx, top - t / 2), (jx, jy)], t)
    right_leg = stroke([(rx, top - t / 2), (jx, jy), (bx, bot + t / 2)], t)
    return Glyph((left_arm, right_leg), (), R + SIDE)


def design_j() -> Glyph:
    t = STEM
    top = X_HEIGHT
    bot = DESCENDER
    cx = SIDE + 88
    hook_r = 108.0
    left, right = cx - t / 2, cx + t / 2
    b = PathBuilder()
    b.moveTo(left, top)
    b.lineTo(right, top)
    b.lineTo(right, bot + hook_r)
    hook_left = left - (hook_r - t)
    b.curveTo(
        right,
        bot + hook_r * (1 - K),
        hook_left + t + hook_r * K,
        bot,
        hook_left + t,
        bot,
    )
    b.lineTo(hook_left, bot)
    b.lineTo(hook_left, bot + t)
    ir = hook_r - t
    b.curveTo(hook_left + ir * K, bot + t, left, bot + t + ir * K, left, bot + hook_r)
    b.lineTo(left, top)
    b.closePath()
    dw, dh = t * 0.88, t * 1.05
    gap = t * 0.48
    dot = rect(cx - dw / 2, top + gap, cx + dw / 2, top + gap + dh)
    return Glyph((b.build(), dot), (), cx + SIDE + 70)


def design_u() -> Glyph:
    t = STEM
    top = X_HEIGHT
    bot = -OVERSHOOT
    L = SIDE
    counter = 295.0
    R = L + t + counter + t
    arc = (R - L) * 0.45
    mid = (L + R) / 2
    b = PathBuilder()
    b.moveTo(L, top)
    b.lineTo(L, bot + arc)
    b.curveTo(L, bot + arc * 0.25, L + arc * 0.25, bot, mid, bot)
    b.curveTo(R - arc * 0.25, bot, R, bot + arc * 0.25, R, bot + arc)
    b.lineTo(R, top)
    b.lineTo(R - t, top)
    b.lineTo(R - t, bot + arc)
    ib = bot + t
    b.curveTo(R - t, ib + (arc - t) * 0.25, R - t - (arc - t) * 0.25, ib, mid, ib)
    b.curveTo(L + t + (arc - t) * 0.25, ib, L + t, ib + (arc - t) * 0.25, L + t, bot + arc)
    b.lineTo(L + t, top)
    b.closePath()
    return Glyph((b.build(),), (), R + SIDE)


DESIGNS = [design_z, design_a, design_y, design_j, design_u]


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def glyph_bounds(g: Glyph) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for o in list(g.outers) + list(g.holes):
        a, b, c, d = bounds(o)
        xs += [a, c]
        ys += [b, d]
    return min(xs), min(ys), max(xs), max(ys)


def _paint_outline(mask: Image.Image, outline: Outline, scale: float, ox: float, by: float, value: int) -> None:
    from typekernel.qa import specimen_png as sp

    md = ImageDraw.Draw(mask)

    def tp(p: Point) -> tuple[float, float]:
        return (ox + p.x * scale, by - p.y * scale)

    for c in outline.contours:
        if c.segments and c.closed:
            poly = sp._sample_contour(c.segments, tp)
            if len(poly) >= 3:
                md.polygon(poly, fill=value)


def render_glyph_rgba(g: Glyph, scale: float, baseline_y: float, w: int, h: int, ox: float) -> Image.Image:
    mask = Image.new("L", (w, h), 0)
    for o in g.outers:
        tmp = Image.new("L", (w, h), 0)
        _paint_outline(tmp, o, scale, ox, baseline_y, 255)
        mask = ImageChops.lighter(mask, tmp)
    for hole in g.holes:
        _paint_outline(mask, hole, scale, ox, baseline_y, 0)
    return Image.composite(Image.new("RGBA", (w, h), FG), Image.new("RGBA", (w, h), (0, 0, 0, 0)), mask)


def render_glyph_png(g: Glyph, path: Path, size: int = 520) -> None:
    min_x, min_y, max_x, max_y = glyph_bounds(g)
    bw, bh = max_x - min_x, max_y - min_y
    margin = 0.1 * size
    drawable = size - 2 * margin
    scale = drawable / max(bw, bh)
    ox = margin + (drawable - bw * scale) / 2 - min_x * scale
    baseline = margin + max_y * scale
    bg = Image.new("RGBA", (size, size), BG)
    gimg = render_glyph_rgba(g, scale, baseline, size, size, ox)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(bg, gimg).convert("RGB").save(path)


def render_word_panel(glyphs: list[Glyph], panel_w: int, panel_h: int, baseline_y: int, target_x_h: float = 92.0) -> Image.Image:
    scale = target_x_h / X_HEIGHT
    tracking = 8.0 * scale
    advances = [g.advance * scale + tracking for g in glyphs]
    content_w = sum(advances) - tracking
    x = (panel_w - content_w) / 2.0
    panel = Image.new("RGBA", (panel_w, panel_h), BG)
    for g, adv in zip(glyphs, advances):
        min_x, _, max_x, _ = glyph_bounds(g)
        pad = 36
        local_w = int((max_x - min_x) * scale) + pad * 2
        ox = pad - min_x * scale
        gimg = render_glyph_rgba(g, scale, float(baseline_y), local_w, panel_h, ox)
        panel.alpha_composite(gimg, (int(x - pad), 0))
        x += adv
    return panel


def _load_anthropic_font(size: int) -> ImageFont.FreeTypeFont:
    from fontTools.ttLib import TTFont

    cache = Path("/tmp/anthro-fonts/AnthropicSans-Roman-Web.woff2")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists() or cache.stat().st_size < 1000:
        print("downloading Anthropic Sans (local demo only, not committed)…")
        req = urllib.request.Request(ANTHROPIC_SANS_WOFF2, headers={"User-Agent": "typekernel-specimen/0.1"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            cache.write_bytes(resp.read())
    font = TTFont(str(cache))
    ttf = cache.with_suffix(".ttf")
    font.flavor = None
    font.save(str(ttf))
    return ImageFont.truetype(str(ttf), size=size)


def _font(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size=size, index=index)
    except OSError:
        return ImageFont.load_default()


def _text_panel(text: str, font: ImageFont.FreeTypeFont, w: int, h: int, baseline: int) -> Image.Image:
    img = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), text, font=font)
    x = (w - (bbox[2] - bbox[0])) // 2 - bbox[0]
    d.text((x, baseline), text, font=font, fill=FG, anchor="ls")
    return img


def compose_compare(glyphs: list[Glyph]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    panel_w, panel_h = 700, 480
    label_h, gap, margin = 72, 20, 32
    total_w = margin * 2 + panel_w * 3 + gap * 2
    total_h = margin * 2 + label_h + panel_h + 28
    baseline = int(panel_h * 0.60)

    apple = _text_panel("zayju", _font(APPLE_FONT, 172), panel_w, panel_h, baseline)
    anthro = _text_panel("zayju", _load_anthropic_font(162), panel_w, panel_h, baseline)
    tk = render_word_panel(glyphs, panel_w, panel_h, baseline)

    canvas = Image.new("RGBA", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)
    title_font = _font(LABEL_FONT, 26)
    sub_font = _font(APPLE_FONT, 16)
    labels = [
        ("苹果系统默认", "SF Pro · SFNS"),
        ("Anthropic", "Anthropic Sans（官网）"),
        ("typekernel 二创", "PathBuilder 几何新无衬线"),
    ]
    for i, (panel, (title, sub)) in enumerate(zip([apple, anthro, tk], labels)):
        x = margin + i * (panel_w + gap)
        y = margin + label_h
        tb = draw.textbbox((0, 0), title, font=title_font)
        draw.text((x + (panel_w - (tb[2] - tb[0])) // 2, margin + 6), title, font=title_font, fill=LABEL_FG)
        sb = draw.textbbox((0, 0), sub, font=sub_font)
        draw.text((x + (panel_w - (sb[2] - sb[0])) // 2, margin + 40), sub, font=sub_font, fill=SUB_FG)
        draw.rectangle([x, y, x + panel_w - 1, y + panel_h - 1], outline=RULE, width=1)
        canvas.paste(panel, (x, y))

    out_ex = OUT_DIR / "compare.png"
    out_docs = DOCS_IMG / COMPARE_NAME
    rgb = canvas.convert("RGB")
    rgb.save(out_ex)
    rgb.save(out_docs)
    print("wrote", out_ex)
    print("wrote", out_docs)
    return out_docs


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    glyphs = [d() for d in DESIGNS]
    for ch, g in zip("zayju", glyphs):
        print(ch, glyph_bounds(g))
        render_glyph_png(g, OUT_DIR / f"letter_{ch}.png")
    render_word_panel(glyphs, 1400, 720, 430, target_x_h=120).convert("RGB").save(OUT_DIR / "zayju_typekernel.png")
    print("wrote", OUT_DIR / "zayju_typekernel.png")
    compose_compare(glyphs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
