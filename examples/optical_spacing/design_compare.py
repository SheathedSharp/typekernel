"""Before/after optical spacing for ``zayju`` (milestone 1 specimen).

Left: heuristic sidebearings + default kern (bbox-even, optically uneven).
Right: optical sidebearings + fitted kern (optically even).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from typekernel.parts import DesignContext, default_sans_kern, layout_glyphs, word_zayju
from typekernel.qa.score import word_report, zayju_report

OUT_DIR = Path(__file__).resolve().parent / "out"
DOCS_IMG = Path(__file__).resolve().parents[2] / "docs" / "images"
NAME = "zayju-optical-spacing-before-after.png"

BG = (255, 255, 255, 255)
FG = (22, 22, 26, 255)
LABEL_FG = (40, 40, 48, 255)
SUB_FG = (120, 120, 130, 255)
RULE = (220, 220, 224, 255)
LABEL_FONT = "/System/Library/Fonts/SFNS.ttf"


def _font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(LABEL_FONT, size=size)
    except OSError:
        return ImageFont.load_default()


def _bake_otf(glyphs, names, path: Path) -> Path:
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.t2CharStringPen import T2CharStringPen

    from typekernel.geo.segment import LineSegment

    ctx = glyphs[0].context
    charstrings: dict = {}
    advances: dict = {}
    order = [".notdef"]
    nd = T2CharStringPen(0, None)
    nd.endPath()
    charstrings[".notdef"] = nd.getCharString()
    advances[".notdef"] = (int(ctx.units_per_em // 2), 0)
    for ch, g in zip(names, glyphs):
        order.append(ch)
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
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({ord(ch): ch for ch in names})
    fb.setupCFF(
        psName="TypekernelSpacingDemo",
        fontInfo={
            "FullName": "Typekernel Spacing Demo",
            "FamilyName": "TypekernelSpacingDemo",
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
            "familyName": "TypekernelSpacingDemo",
            "styleName": "Regular",
            "uniqueFontIdentifier": "typekernel-spacing-demo",
            "fullName": "Typekernel Spacing Demo",
            "psName": "TypekernelSpacingDemo-Regular",
            "version": "0.1",
        }
    )
    out = path.with_suffix(".otf")
    out.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(out))
    return out


def _render_word(glyphs, names, kerning, panel_w, panel_h, baseline, target_x_h) -> Image.Image:
    ctx = glyphs[0].context
    scale = target_x_h / ctx.x_height
    px = max(12, round(ctx.units_per_em * scale))
    font_path = _bake_otf(glyphs, names, OUT_DIR / f"_tmp_{''.join(names)}")
    font = ImageFont.truetype(str(font_path), size=px)
    xs = layout_glyphs(glyphs, names, kerning=kerning)
    xs_px = [x * scale for x in xs]
    advances = [g.advance * scale for g in glyphs]
    content_w = xs_px[-1] + advances[-1]
    x0 = (panel_w - content_w) / 2.0
    ss = 3
    big = Image.new("RGBA", (panel_w * ss, panel_h * ss), BG)
    draw = ImageDraw.Draw(big)
    try:
        scaled = font.font_variant(size=px * ss)  # type: ignore[attr-defined]
    except (AttributeError, TypeError, OSError):
        scaled = font
    for ch, x in zip(names, xs_px):
        draw.text(((x0 + x) * ss, baseline * ss), ch, font=scaled, fill=FG, anchor="ls")
    return big.resize((panel_w, panel_h), resample=Image.Resampling.LANCZOS)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    ctx = DesignContext.geometric_sans()
    names = list("zayju")

    before_glyphs = word_zayju(ctx)
    before_kern = default_sans_kern()
    before_rep = word_report(before_glyphs, names, kerning=before_kern)
    after_rep, after_glyphs, after_kern = zayju_report(ctx, optical=True)

    before_rep.write_json(OUT_DIR / "before.json")
    after_rep.write_json(OUT_DIR / "after.json")

    panel_w, panel_h = 900, 420
    label_h, gap, margin = 88, 24, 28
    total_w = margin * 2 + panel_w * 2 + gap
    total_h = margin * 2 + label_h + panel_h + 20
    baseline = int(panel_h * 0.62)
    target_x_h = 100.0

    canvas = Image.new("RGBA", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)
    title_f = _font(26)
    sub_f = _font(14)

    panels = [
        (
            "Before — heuristic spacing",
            f"bbox ratio {before_rep.bbox_gap_ratio:.2f} · optical ratio {before_rep.optical_gap_ratio:.2f} · stem CV {before_rep.stem_cv:.3f}",
            before_glyphs,
            before_kern,
        ),
        (
            "After — optical spacing",
            f"bbox ratio {after_rep.bbox_gap_ratio:.2f} · optical ratio {after_rep.optical_gap_ratio:.2f} · stem CV {after_rep.stem_cv:.3f}",
            after_glyphs,
            after_kern,
        ),
    ]
    for i, (title, sub, glyphs, kern) in enumerate(panels):
        panel = _render_word(glyphs, names, kern, panel_w, panel_h, baseline, target_x_h)
        x = margin + i * (panel_w + gap)
        y = margin + label_h
        tb = draw.textbbox((0, 0), title, font=title_f)
        draw.text(
            (x + (panel_w - (tb[2] - tb[0])) // 2, margin + 8),
            title,
            font=title_f,
            fill=LABEL_FG,
        )
        sb = draw.textbbox((0, 0), sub, font=sub_f)
        draw.text(
            (x + (panel_w - (sb[2] - sb[0])) // 2, margin + 44),
            sub,
            font=sub_f,
            fill=SUB_FG,
        )
        draw.rectangle([x, y, x + panel_w - 1, y + panel_h - 1], outline=RULE, width=1)
        canvas.paste(panel, (x, y))

    out_ex = OUT_DIR / "compare.png"
    out_docs = DOCS_IMG / NAME
    rgb = canvas.convert("RGB")
    rgb.save(out_ex, optimize=True)
    rgb.save(out_docs, optimize=True)
    print("before", before_rep.to_dict())
    print("after", after_rep.to_dict())
    print("wrote", out_ex)
    print("wrote", out_docs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
