"""Three original typekernel directions for ``zayju`` (paper + code brief).

No commercial reference columns. Each panel is a related DesignContext on the
same parts recipes: Ink Book, Code Clear, Open Print.

Bake composed cubics to CFF/OTF and rasterize with FreeType (via Pillow) so
counters stay open — not PIL polygon fill.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from typekernel.geo.layout import union_bounds
from typekernel.geo.segment import LineSegment
from typekernel.parts import (
    ComposedGlyph,
    FormSources,
    DesignContext,
    default_sans_kern,
    layout_glyphs,
)

OUT_DIR = Path(__file__).resolve().parent / "out"
DOCS_IMG = Path(__file__).resolve().parents[2] / "docs" / "images"
SPECIMEN_NAME = "zayju-paper-code-triad.png"

BG = (255, 255, 255, 255)
FG = (22, 22, 26, 255)
LABEL_FG = (40, 40, 48, 255)
SUB_FG = (120, 120, 130, 255)
RULE = (220, 220, 224, 255)

LABEL_FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FALLBACK_FONT = "/System/Library/Fonts/SFNS.ttf"

DIRECTIONS: list[tuple[str, str, DesignContext]] = [
    (
        "Ink Book",
        "paper · solid stems · open counters",
        DesignContext.paper_ink(),
    ),
    (
        "Code Clear",
        "coding · tall x-height · even spacing",
        DesignContext.code_clear(),
    ),
    (
        "Open Print",
        "print · soft joins · wide aperture",
        DesignContext.open_print(),
    ),
]


def _font(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size=size, index=index)
    except OSError:
        try:
            return ImageFont.truetype(FALLBACK_FONT, size=size)
        except OSError:
            return ImageFont.load_default()


def bake_otf(glyphs: list[ComposedGlyph], names: list[str], path: Path) -> Path:
    """Bake typekernel cubics to CFF OpenType (our outlines, our advances)."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.t2CharStringPen import T2CharStringPen

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
                        pen.curveTo(
                            (seg.p1.x, seg.p1.y),
                            (seg.p2.x, seg.p2.y),
                            (seg.p3.x, seg.p3.y),
                        )
                if contour.closed:
                    pen.closePath()
        charstrings[ch] = pen.getCharString()
        advances[ch] = (width, 0)

    fb = FontBuilder(int(ctx.units_per_em), isTTF=False)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap({ord(ch): ch for ch in names})
    fb.setupCFF(
        psName="TypekernelPaperCode",
        fontInfo={
            "FullName": "Typekernel Paper Code",
            "FamilyName": "TypekernelPaperCode",
            "Weight": "Regular",
        },
        privateDict={},
        charStringsDict=charstrings,
    )
    fb.setupHorizontalMetrics(advances)
    fb.setupHorizontalHeader(ascent=int(ctx.ascender), descent=int(ctx.descender))
    fb.setupOS2(
        sTypoAscender=int(ctx.ascender),
        sTypoDescender=int(ctx.descender),
        sxHeight=int(ctx.x_height),
    )
    fb.setupPost()
    fb.setupNameTable(
        {
            "familyName": "TypekernelPaperCode",
            "styleName": "Regular",
            "uniqueFontIdentifier": "typekernel-paper-code",
            "fullName": "Typekernel Paper Code",
            "psName": "TypekernelPaperCode-Regular",
            "version": "0.1",
        }
    )
    out = path.with_suffix(".otf")
    out.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(out))
    return out


def render_word_ft(
    glyphs: list[ComposedGlyph],
    names: list[str],
    font_path: Path,
    panel_w: int,
    panel_h: int,
    baseline: int,
    target_x_h: float,
) -> Image.Image:
    """FreeType-rasterize each glyph and place with our kerning layout."""
    ctx = glyphs[0].context
    scale = target_x_h / ctx.x_height
    # Pillow size is in pixels ≈ design units * scale for x-height match
    px = max(12, round(ctx.units_per_em * scale))
    font = ImageFont.truetype(str(font_path), size=px)
    xs = layout_glyphs(
        glyphs,
        names,
        tracking=ctx.tracking,
        kerning=default_sans_kern(),
    )
    advances = [g.advance * scale for g in glyphs]
    xs_px = [x * scale for x in xs]
    content_w = xs_px[-1] + advances[-1] if glyphs else 0.0
    x0 = (panel_w - content_w) / 2.0

    ss = 3
    big = Image.new("RGBA", (panel_w * ss, panel_h * ss), BG)
    draw = ImageDraw.Draw(big)
    try:
        scaled_font = font.font_variant(size=px * ss)  # type: ignore[attr-defined]
    except (AttributeError, TypeError, OSError):
        scaled_font = font

    for ch, x in zip(names, xs_px):
        draw.text(
            ((x0 + x) * ss, baseline * ss),
            ch,
            font=scaled_font,
            fill=FG,
            anchor="ls",
        )
    return big.resize((panel_w, panel_h), resample=Image.Resampling.LANCZOS)


def compose_triad() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_IMG.mkdir(parents=True, exist_ok=True)

    panel_w, panel_h = 680, 460
    label_h, gap, margin = 78, 18, 28
    total_w = margin * 2 + panel_w * 3 + gap * 2
    total_h = margin * 2 + label_h + panel_h + 24
    baseline = int(panel_h * 0.62)
    target_x_h = 96.0

    canvas = Image.new("RGBA", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)
    title_font = _font(LABEL_FONT, 28)
    sub_font = _font(FALLBACK_FONT, 15)

    for i, (title, sub, ctx) in enumerate(DIRECTIONS):
        # Specimen/compose-time derive from locked FormSources (not DesignSequence design; phrase is late proof only).
        drawn = FormSources.from_context(ctx).derive("zayju")
        glyphs = [drawn[ch] for ch in "zayju"]
        names = list("zayju")
        font_path = bake_otf(glyphs, names, OUT_DIR / f"zayju_{title.lower().replace(' ', '_')}")
        for ch, g in zip(names, glyphs):
            box = union_bounds(list(g.solids) + list(g.holes))
            print(f"{title} {ch}: adv={g.advance:.1f} ink={box[2]-box[0]:.1f}")
        panel = render_word_ft(
            glyphs, names, font_path, panel_w, panel_h, baseline, target_x_h
        )
        x = margin + i * (panel_w + gap)
        y = margin + label_h
        tb = draw.textbbox((0, 0), title, font=title_font)
        draw.text(
            (x + (panel_w - (tb[2] - tb[0])) // 2, margin + 8),
            title,
            font=title_font,
            fill=LABEL_FG,
        )
        sb = draw.textbbox((0, 0), sub, font=sub_font)
        draw.text(
            (x + (panel_w - (sb[2] - sb[0])) // 2, margin + 44),
            sub,
            font=sub_font,
            fill=SUB_FG,
        )
        draw.rectangle([x, y, x + panel_w - 1, y + panel_h - 1], outline=RULE, width=1)
        canvas.paste(panel, (x, y))

    out_ex = OUT_DIR / "triad.png"
    out_docs = DOCS_IMG / SPECIMEN_NAME
    rgb = canvas.convert("RGB")
    rgb.save(out_ex, optimize=True)
    rgb.save(out_docs, optimize=True)
    print("wrote", out_ex)
    print("wrote", out_docs)
    return out_docs


def main() -> int:
    compose_triad()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
