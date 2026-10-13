"""Recreate the word "zayju" with typekernel parts and compare three styles.

Columns: Apple system default | Anthropic Sans (site font) | typekernel recreation.

The typekernel column is assembled like Three.js meshes: one shared
``DesignContext``, reusable parts (stem, bowl, fillet pads, hook, …),
boolean joins when pathops is available, and minimal kerning — not one-off
hard paths. See ``examples/agent_catalog/`` for the full agent API index.

Requires::

    pip install -e ".[specimen,boolean]" && pip install brotli

The middle column downloads Anthropic Sans for local comparison only (cached
under /tmp; never committed).
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from typekernel.geo.layout import union_bounds
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.parts import (
    ComposedGlyph,
    Controls,
    DesignContext,
    default_sans_kern,
    layout_glyphs,
)

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

# One shared rhythm for the whole word — the parts-layer point.
CTX = DesignContext.geometric_sans().tuned(tracking=0.0, sidebearing_ratio=0.04)


def _ink_outlines(g: ComposedGlyph) -> list[Outline]:
    return list(g.solids) + list(g.holes)


def glyph_bounds(g: ComposedGlyph) -> tuple[float, float, float, float]:
    return union_bounds(_ink_outlines(g))


def _contour_abs_area(contour) -> float:
    """Approximate absolute polygon area from on-curve starts (sort key)."""
    pts = [seg.points[0] for seg in contour.segments]
    if len(pts) < 3:
        return 0.0
    pts.append(contour.segments[-1].points[-1])
    area = 0.0
    for i in range(len(pts) - 1):
        area += pts[i].x * pts[i + 1].y - pts[i + 1].x * pts[i].y
    return abs(area) * 0.5


def _paint_outline_evenodd(
    mask: Image.Image,
    outline: Outline,
    scale: float,
    ox: float,
    by: float,
    *,
    samples: int,
) -> None:
    """True even-odd fill: XOR each closed contour into ``mask``.

    Neo-grotesque sources often use overlapping same-winding contours that only
    resolve under even-odd (not "largest minus rest"). Binary XOR via
    :func:`ImageChops.difference` implements that rule.
    """
    from typekernel.qa import specimen_png as sp

    def tp(p: Point) -> tuple[float, float]:
        return (ox + p.x * scale, by - p.y * scale)

    for c in outline.contours:
        if not (c.segments and c.closed):
            continue
        poly = sp._sample_contour(c.segments, tp, samples=samples)
        if len(poly) < 3:
            continue
        layer = Image.new("L", mask.size, 0)
        ImageDraw.Draw(layer).polygon(poly, fill=255)
        # difference on {0,255} is XOR → even-odd accumulation
        xor = ImageChops.difference(mask, layer)
        mask.paste(xor)


def render_glyph_rgba(
    g: ComposedGlyph,
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
    for o in g.solids:
        tmp = Image.new("L", (rw, rh), 0)
        _paint_outline_evenodd(tmp, o, scale_ss, ox_ss, by_ss, samples=samples)
        mask = ImageChops.lighter(mask, tmp)
    for hole in g.holes:
        # Explicit holes always punch (may contain one or more contours)
        from typekernel.qa import specimen_png as sp

        md = ImageDraw.Draw(mask)

        def tp(p: Point, _ox=ox_ss, _by=by_ss, _sc=scale_ss) -> tuple[float, float]:
            return (_ox + p.x * _sc, _by - p.y * _sc)

        for c in hole.contours:
            if c.segments and c.closed:
                poly = sp._sample_contour(c.segments, tp, samples=samples)
                if len(poly) >= 3:
                    md.polygon(poly, fill=0)
    big = Image.composite(
        Image.new("RGBA", (rw, rh), FG),
        Image.new("RGBA", (rw, rh), (0, 0, 0, 0)),
        mask,
    )
    if supersample > 1:
        big = big.resize((w, h), resample=Image.Resampling.LANCZOS)
    return big


def render_glyph_png(g: ComposedGlyph, path: Path, size: int = 520) -> None:
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
    glyphs: list[ComposedGlyph],
    panel_w: int,
    panel_h: int,
    baseline_y: int,
    target_x_h: float = 92.0,
    names: list[str] | None = None,
) -> Image.Image:
    scale = target_x_h / CTX.x_height
    # layout_glyphs works in design units; scale positions afterward.
    xs_du = layout_glyphs(
        glyphs,
        names,
        tracking=CTX.tracking,
        kerning=default_sans_kern() if names else None,
    )
    advances = [g.advance * scale for g in glyphs]
    xs = [x * scale for x in xs_du]
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
    ss = 3
    img = Image.new("RGBA", (w * ss, h * ss), BG)
    d = ImageDraw.Draw(img)
    try:
        scaled = font.font_variant(size=font.size * ss)  # type: ignore[attr-defined]
    except (AttributeError, TypeError, OSError):
        scaled = font
    bbox = d.textbbox((0, 0), text, font=scaled)
    x = (w * ss - (bbox[2] - bbox[0])) // 2 - bbox[0]
    d.text((x, baseline * ss), text, font=scaled, fill=FG, anchor="ls")
    return img.resize((w, h), resample=Image.Resampling.LANCZOS)





def bake_word_ttf(glyphs: list[ComposedGlyph], names: list[str], path: Path) -> Path:
    """Bake typekernel composed outlines (CFF/OTF). No commercial outline paste."""
    return _bake_from_composed(glyphs, names, path)


def _bake_from_composed(glyphs: list[ComposedGlyph], names: list[str], path: Path) -> Path:
    """Fallback: bake from typekernel Outline cubics via CFF."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.t2CharStringPen import T2CharStringPen

    from typekernel.geo.segment import LineSegment

    ctx = glyphs[0].context
    charstrings: dict = {}
    advances: dict = {}
    glyph_order = [".notdef"]
    nd = T2CharStringPen(0, None)
    nd.endPath()
    charstrings[".notdef"] = nd.getCharString()
    advances[".notdef"] = (int(ctx.units_per_em // 2), 0)
    for ch, g in zip(names, glyphs):
        glyph_order.append(ch)
        width = max(1, round(g.advance))
        pen = T2CharStringPen(width, None)
        for solid in list(g.solids) + list(g.holes):
            for contour in solid.contours:
                if not contour.segments:
                    continue
                start = contour.segments[0].points[0]
                pen.moveTo((start.x, start.y))
                for seg in contour.segments:
                    if isinstance(seg, LineSegment):
                        pen.lineTo((seg.p1.x, seg.p1.y))
                    else:
                        pen.curveTo((seg.p1.x, seg.p1.y), (seg.p2.x, seg.p2.y), (seg.p3.x, seg.p3.y))
                if contour.closed:
                    pen.closePath()
        charstrings[ch] = pen.getCharString()
        advances[ch] = (width, 0)
    fb = FontBuilder(int(ctx.units_per_em), isTTF=False)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({ord(ch): ch for ch in names})
    fb.setupCFF(psName="TypekernelZayju-Regular", fontInfo={"FullName": "Typekernel Zayju Demo", "FamilyName": "TypekernelZayju", "Weight": "Regular"}, privateDict={}, charStringsDict=charstrings)
    fb.setupHorizontalMetrics(advances)
    fb.setupHorizontalHeader(ascent=int(ctx.ascender), descent=int(ctx.descender))
    fb.setupOS2(sTypoAscender=int(ctx.ascender), sTypoDescender=int(ctx.descender), sxHeight=int(ctx.x_height))
    fb.setupPost()
    fb.setupNameTable({"familyName": "TypekernelZayju", "styleName": "Regular", "uniqueFontIdentifier": "typekernel-zayju-demo", "fullName": "Typekernel Zayju Demo", "psName": "TypekernelZayju-Regular", "version": "0.1"})
    out = path.with_suffix(".otf")
    out.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(out))
    return out


def compose_compare(glyphs: list[ComposedGlyph]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    panel_w, panel_h = 700, 480
    label_h, gap, margin = 72, 20, 32
    total_w = margin * 2 + panel_w * 3 + gap * 2
    total_h = margin * 2 + label_h + panel_h + 28
    baseline = int(panel_h * 0.60)

    apple = _text_panel("zayju", _font(APPLE_FONT, 172), panel_w, panel_h, baseline)
    anthro = _text_panel("zayju", _load_anthropic_font(162), panel_w, panel_h, baseline)
    # Bake typekernel outlines to TTF so FreeType applies the same fill rules
    # as the middle column (fixes even-odd / winding artifacts from PIL polygons).
    font_path = bake_word_ttf(glyphs, list("zayju"), OUT_DIR / "typekernel_zayju.ttf")
    tk = _text_panel("zayju", ImageFont.truetype(str(font_path), size=162), panel_w, panel_h, baseline)

    canvas = Image.new("RGBA", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)
    title_font = _font(LABEL_FONT, 26)
    sub_font = _font(APPLE_FONT, 16)
    labels = [
        ("苹果系统默认", "SF Pro · SFNS"),
        ("Anthropic", "Anthropic Sans（官网）"),
        ("typekernel 二创", "neo-grotesque · matched stems · AA"),
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
    drawn = Controls.from_context(CTX).build_all("zayju")
    glyphs = [drawn[ch] for ch in "zayju"]
    for ch, g in zip("zayju", glyphs):
        print(ch, "advance=", round(g.advance, 1), "bounds=", glyph_bounds(g))
        render_glyph_png(g, OUT_DIR / f"letter_{ch}.png")
    font_path = bake_word_ttf(glyphs, list("zayju"), OUT_DIR / "typekernel_zayju.ttf")
    word = _text_panel("zayju", ImageFont.truetype(str(font_path), size=200), 1400, 720, 430)
    word.convert("RGB").save(OUT_DIR / "zayju_typekernel.png", optimize=True)
    print("wrote", OUT_DIR / "zayju_typekernel.png")
    compose_compare(glyphs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
