"""Recreate the word "zayju" with typekernel and compare three styles.

Columns: Apple system default | Anthropic Sans (site font) | typekernel recreation.

Design intent for the typekernel column: geometric neo-grotesque inspired by
Anthropic Sans — even stems, single-story a, open apertures, softer cubic joins.
Not a copy of Anthropic metrics; not based on zayJu.

Run::

    pip install -e ".[specimen]" && pip install brotli
    python examples/anthropic_zayju/design_zayju.py

The middle column downloads Anthropic Sans for local comparison only (cached
under /tmp; never committed).
"""

from __future__ import annotations

import math
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from typekernel.geo import Outline, PathBuilder
from typekernel.geo.contour import Contour
from typekernel.geo.layout import layout_x_positions, union_bounds
from typekernel.geo.path_helpers import KAPPA, smooth_cubic_controls
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.context import OpticalContext
from typekernel.optics.sidebearing import suggest_sidebearings

# Design space (1000 UPM-ish)
X_HEIGHT = 520.0
STEM = 72.0
OVERSHOOT = 10.0
DESCENDER = -210.0
SIDE_FALLBACK = 48.0

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

CTX = OpticalContext(
    units_per_em=1000.0,
    x_height=X_HEIGHT,
    cap_height=700.0,
    overshoot_round=OVERSHOOT,
)


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


def _ink_outlines(g: Glyph) -> list[Outline]:
    return list(g.outers) + list(g.holes)


def _with_sidebearings(outers: tuple[Outline, ...], holes: tuple[Outline, ...]) -> Glyph:
    """Pack ink to origin-aware advance using suggested sidebearings."""
    box = union_bounds(list(outers) + list(holes)) if holes else union_bounds(list(outers))
    # Temporary outline for SB heuristic: use outer union bounds as a rect proxy.
    proxy = PathBuilder()
    proxy.moveTo(box[0], box[1])
    proxy.lineTo(box[2], box[1])
    proxy.lineTo(box[2], box[3])
    proxy.lineTo(box[0], box[3])
    proxy.closePath()
    left, right = suggest_sidebearings(proxy.build(), CTX)
    # Shift so leftmost ink sits at `left`.
    dx = left - box[0]
    outers_t = tuple(translate_outline(o, dx) for o in outers)
    holes_t = tuple(translate_outline(h, dx) for h in holes)
    ink_w = box[2] - box[0]
    advance = left + ink_w + right
    return Glyph(outers_t, holes_t, advance)


def oval(cx: float, cy: float, rx: float, ry: float) -> Outline:
    b = PathBuilder()
    b.addEllipse(cx, cy, rx, ry)
    return b.build()


def rect(x0: float, y0: float, x1: float, y1: float) -> Outline:
    b = PathBuilder()
    b.moveTo(x0, y0)
    b.lineTo(x1, y0)
    b.lineTo(x1, y1)
    b.lineTo(x0, y1)
    b.closePath()
    return b.build()


def stroke_polyline(
    pts: list[tuple[float, float]], thickness: float, *, join_radius: float = 0.0
) -> Outline:
    """Centered stroke of a polyline with optional rounded corners at joins."""
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
                m = min(1.0 / max(dot, 0.45), 2.2)
                nx, ny = nx * m, ny * m
        left.append((pts[i][0] + nx * half, pts[i][1] + ny * half))
        right.append((pts[i][0] - nx * half, pts[i][1] - ny * half))

    b = PathBuilder()
    if join_radius <= 0 or n < 3:
        b.moveTo(*left[0])
        for pt in left[1:]:
            b.lineTo(*pt)
        b.lineTo(*right[-1])
        for pt in reversed(right[:-1]):
            b.lineTo(*pt)
        b.closePath()
        return b.build()

    b.moveTo(*left[0])
    for i in range(1, len(left) - 1):
        b.roundedCornerTo(left[i][0], left[i][1], left[i + 1][0], left[i + 1][1], join_radius, continue_to_end=False)
    b.lineTo(*left[-1])
    b.lineTo(*right[-1])
    for i in range(len(right) - 2, 0, -1):
        nxt = right[i - 1]
        b.roundedCornerTo(right[i][0], right[i][1], nxt[0], nxt[1], join_radius, continue_to_end=False)
    b.lineTo(*right[0])
    b.closePath()
    return b.build()


# ---------------------------------------------------------------------------
# Letters — geometric, even stem, softer joins
# ---------------------------------------------------------------------------


def design_z() -> Glyph:
    t = STEM
    top = X_HEIGHT
    width = 400.0
    L, R = 0.0, width
    # Continuous Z spine with softened elbows.
    cl = [
        (L + t * 0.15, top - t / 2),
        (R - t * 0.15, top - t / 2),
        (L + t * 0.15, t / 2),
        (R - t * 0.15, t / 2),
    ]
    return _with_sidebearings((stroke_polyline(cl, t, join_radius=t * 0.22),), ())


def design_a() -> Glyph:
    """Single-story geometric a: bowl + right stem, open and even."""
    t = STEM
    top = X_HEIGHT + OVERSHOOT * 0.4
    bot = -OVERSHOOT
    ro = (top - bot) / 2.0
    ri = ro - t
    cx = ro
    cy = (top + bot) / 2.0
    outer = oval(cx, cy, ro, ro)
    hole = oval(cx, cy, ri, ri)
    # Stem: soft top via slight overshoot; sits on the bowl's right.
    stem_left = cx + ri * 0.38
    stem_right = stem_left + t
    stem = rect(stem_left, 0.0, stem_right, top + 2)
    return _with_sidebearings((outer, stem), (hole,))


def design_y() -> Glyph:
    t = STEM
    top = X_HEIGHT
    bot = DESCENDER
    width = 430.0
    L, R = 0.0, width
    jx = (L + R) / 2 - 4
    jy = t * 0.55
    lx, rx = L + t * 0.85, R - t * 0.85
    bx = jx + 40
    left_arm = stroke_polyline([(lx, top - t / 2), (jx, jy)], t, join_radius=0)
    right_leg = stroke_polyline(
        [(rx, top - t / 2), (jx, jy), (bx, bot + t / 2)],
        t,
        join_radius=t * 0.28,
    )
    return _with_sidebearings((left_arm, right_leg), ())


def design_j() -> Glyph:
    t = STEM
    top = X_HEIGHT
    bot = DESCENDER
    cx = 70.0
    hook_r = 100.0
    left, right = cx - t / 2, cx + t / 2
    hook_left = left - (hook_r - t)
    center_x = hook_left + hook_r
    center_y = bot + hook_r

    b = PathBuilder()
    b.moveTo(left, top)
    b.lineTo(right, top)
    b.lineTo(right, bot + hook_r)
    # Outer hook: 0° → -90° (east to south) around the hook centre.
    b.arcTo(center_x, center_y, hook_r, hook_r, -90, start_angle_deg=0)
    b.lineTo(hook_left, bot)
    b.lineTo(hook_left, bot + t)
    ir = hook_r - t
    b.curveTo(
        hook_left + ir * KAPPA,
        bot + t,
        left,
        bot + t + ir * KAPPA,
        left,
        bot + hook_r,
    )
    b.lineTo(left, top)
    b.closePath()
    dw, dh = t * 0.9, t * 1.05
    gap = t * 0.5
    dot = rect(cx - dw / 2, top + gap, cx + dw / 2, top + gap + dh)
    return _with_sidebearings((b.build(), dot), ())


def design_u() -> Glyph:
    t = STEM
    top = X_HEIGHT
    bot = -OVERSHOOT
    counter = 280.0
    L = 0.0
    R = L + t + counter + t
    mid = (L + R) / 2
    # Outer trough with smooth_cubic_controls for even bowl.
    arc_depth = (R - L) * 0.48
    b = PathBuilder()
    b.moveTo(L, top)
    b.lineTo(L, bot + arc_depth)
    p0 = Point(L, bot + arc_depth)
    p3 = Point(mid, bot)
    c1, c2 = smooth_cubic_controls(p0, p3, Point(0, -1), Point(1, 0), handle_ratio=0.45)
    b.curveTo(c1.x, c1.y, c2.x, c2.y, p3.x, p3.y)
    p0 = p3
    p3 = Point(R, bot + arc_depth)
    c1, c2 = smooth_cubic_controls(p0, p3, Point(1, 0), Point(0, 1), handle_ratio=0.45)
    b.curveTo(c1.x, c1.y, c2.x, c2.y, p3.x, p3.y)
    b.lineTo(R, top)
    b.lineTo(R - t, top)
    b.lineTo(R - t, bot + arc_depth)
    ib = bot + t
    inner_depth = arc_depth - t
    p0 = Point(R - t, bot + arc_depth)
    p3 = Point(mid, ib)
    c1, c2 = smooth_cubic_controls(p0, p3, Point(0, -1), Point(-1, 0), handle_ratio=0.45)
    b.curveTo(c1.x, c1.y, c2.x, c2.y, p3.x, p3.y)
    p0 = p3
    p3 = Point(L + t, bot + arc_depth)
    c1, c2 = smooth_cubic_controls(p0, p3, Point(-1, 0), Point(0, 1), handle_ratio=0.45)
    b.curveTo(c1.x, c1.y, c2.x, c2.y, p3.x, p3.y)
    b.lineTo(L + t, top)
    b.closePath()
    return _with_sidebearings((b.build(),), ())


DESIGNS = [design_z, design_a, design_y, design_j, design_u]


# ---------------------------------------------------------------------------
# Render (supersampled)
# ---------------------------------------------------------------------------


def glyph_bounds(g: Glyph) -> tuple[float, float, float, float]:
    return union_bounds(_ink_outlines(g))


def _paint_outline(
    mask: Image.Image,
    outline: Outline,
    scale: float,
    ox: float,
    by: float,
    value: int,
    *,
    samples: int,
) -> None:
    from typekernel.qa import specimen_png as sp

    md = ImageDraw.Draw(mask)

    def tp(p: Point) -> tuple[float, float]:
        return (ox + p.x * scale, by - p.y * scale)

    for c in outline.contours:
        if c.segments and c.closed:
            poly = sp._sample_contour(c.segments, tp, samples=samples)
            if len(poly) >= 3:
                md.polygon(poly, fill=value)


def render_glyph_rgba(
    g: Glyph,
    scale: float,
    baseline_y: float,
    w: int,
    h: int,
    ox: float,
    *,
    supersample: int = 4,
) -> Image.Image:
    rw, rh = w * supersample, h * supersample
    scale_ss = scale * supersample
    ox_ss = ox * supersample
    by_ss = baseline_y * supersample
    samples = 32 * max(1, supersample // 2)
    mask = Image.new("L", (rw, rh), 0)
    for o in g.outers:
        tmp = Image.new("L", (rw, rh), 0)
        _paint_outline(tmp, o, scale_ss, ox_ss, by_ss, 255, samples=samples)
        mask = ImageChops.lighter(mask, tmp)
    for hole in g.holes:
        _paint_outline(mask, hole, scale_ss, ox_ss, by_ss, 0, samples=samples)
    big = Image.composite(
        Image.new("RGBA", (rw, rh), FG),
        Image.new("RGBA", (rw, rh), (0, 0, 0, 0)),
        mask,
    )
    if supersample > 1:
        big = big.resize((w, h), resample=Image.Resampling.LANCZOS)
    return big


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
    Image.alpha_composite(bg, gimg).convert("RGB").save(path, optimize=True)


def render_word_panel(
    glyphs: list[Glyph],
    panel_w: int,
    panel_h: int,
    baseline_y: int,
    target_x_h: float = 92.0,
) -> Image.Image:
    scale = target_x_h / X_HEIGHT
    tracking = 6.0 * scale
    advances = [g.advance * scale for g in glyphs]
    xs = layout_x_positions(advances, tracking=tracking)
    content_w = xs[-1] + advances[-1] if glyphs else 0
    x0 = (panel_w - content_w) / 2.0
    panel = Image.new("RGBA", (panel_w, panel_h), BG)
    for g, adv, x in zip(glyphs, advances, xs):
        min_x, _, max_x, _ = glyph_bounds(g)
        pad = 40
        local_w = int((max_x - min_x) * scale) + pad * 2
        ox = pad - min_x * scale
        gimg = render_glyph_rgba(g, scale, float(baseline_y), local_w, panel_h, ox)
        panel.alpha_composite(gimg, (int(x0 + x - pad), 0))
    return panel


def _load_anthropic_font(size: int) -> ImageFont.FreeTypeFont:
    from fontTools.ttLib import TTFont

    cache = Path("/tmp/anthro-fonts/AnthropicSans-Roman-Web.woff2")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists() or cache.stat().st_size < 1000:
        print("downloading Anthropic Sans (local demo only, not committed)…")
        req = urllib.request.Request(
            ANTHROPIC_SANS_WOFF2, headers={"User-Agent": "typekernel-specimen/0.1"}
        )
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


def _text_panel(
    text: str, font: ImageFont.FreeTypeFont, w: int, h: int, baseline: int
) -> Image.Image:
    # Render large then downsample for softer system-font edges.
    ss = 3
    img = Image.new("RGBA", (w * ss, h * ss), BG)
    d = ImageDraw.Draw(img)
    # Scale font
    try:
        scaled = font.font_variant(size=font.size * ss)  # type: ignore[attr-defined]
    except Exception:
        scaled = font
    bbox = d.textbbox((0, 0), text, font=scaled)
    x = (w * ss - (bbox[2] - bbox[0])) // 2 - bbox[0]
    d.text((x, baseline * ss), text, font=scaled, fill=FG, anchor="ls")
    return img.resize((w, h), resample=Image.Resampling.LANCZOS)


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
        ("typekernel 二创", "几何新无衬线 · 抗锯齿预览"),
    ]
    for i, (panel, (title, sub)) in enumerate(zip([apple, anthro, tk], labels)):
        x = margin + i * (panel_w + gap)
        y = margin + label_h
        tb = draw.textbbox((0, 0), title, font=title_font)
        draw.text(
            (x + (panel_w - (tb[2] - tb[0])) // 2, margin + 6),
            title,
            font=title_font,
            fill=LABEL_FG,
        )
        sb = draw.textbbox((0, 0), sub, font=sub_font)
        draw.text(
            (x + (panel_w - (sb[2] - sb[0])) // 2, margin + 40),
            sub,
            font=sub_font,
            fill=SUB_FG,
        )
        draw.rectangle([x, y, x + panel_w - 1, y + panel_h - 1], outline=RULE, width=1)
        canvas.paste(panel, (x, y))

    out_ex = OUT_DIR / "compare.png"
    out_docs = DOCS_IMG / COMPARE_NAME
    rgb = canvas.convert("RGB")
    rgb.save(out_ex, optimize=True)
    rgb.save(out_docs, optimize=True)
    print("wrote", out_ex)
    print("wrote", out_docs)
    return out_docs


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    glyphs = [d() for d in DESIGNS]
    for ch, g in zip("zayju", glyphs):
        print(ch, "advance=", round(g.advance, 1), "bounds=", glyph_bounds(g))
        render_glyph_png(g, OUT_DIR / f"letter_{ch}.png")
    render_word_panel(glyphs, 1400, 720, 430, target_x_h=120).convert("RGB").save(
        OUT_DIR / "zayju_typekernel.png", optimize=True
    )
    print("wrote", OUT_DIR / "zayju_typekernel.png")
    compose_compare(glyphs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
