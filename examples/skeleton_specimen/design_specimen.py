"""Multi-panel specimen: control glyphs → related forms → optical infra.

Designer workflow: DesignContext proportions → build_n / build_o → h_from_n
→ space_word_optical / auto_class_kern → FreeType raster. Paper + coding
contexts; no face-specific hacks.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from typekernel.geo.segment import LineSegment
from typekernel.optics.space import space_word_optical
from typekernel.parts import (
    ComposedGlyph,
    DesignContext,
    KernClass,
    auto_class_kern,
    build_control_word,
    build_n,
    build_o,
    h_from_n,
    layout_glyphs,
    rhythm_from_control_glyphs,
)
from typekernel.qa.score import word_report

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
DOCS_IMG = HERE.parents[1] / "docs" / "images"
NAME = "skeleton-infra-specimen.png"

BG = (255, 255, 255)
FG = (22, 22, 26)
SUB = (100, 100, 110)
RULE = (220, 220, 224)
ACCENT = (40, 110, 200)

WORD = "ohio"
LABEL_FONT = "/System/Library/Fonts/SFNS.ttf"
FALLBACK = "/System/Library/Fonts/Helvetica.ttc"

CONTEXTS: list[tuple[str, str, DesignContext]] = [
    ("Ink Book", "paper_ink · durable stems · open counters", DesignContext.paper_ink()),
    ("Code Clear", "code_clear · tall x-height · even colour", DesignContext.code_clear()),
    ("Open Print", "open_print · soft joins · wide aperture", DesignContext.open_print()),
]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (LABEL_FONT, FALLBACK):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def bake_otf(glyphs: list[ComposedGlyph], names: list[str], path: Path) -> Path:
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

    for ch, g in zip(names, glyphs, strict=True):
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
        psName="TypekernelSkeleton",
        fontInfo={
            "FullName": "Typekernel Skeleton",
            "FamilyName": "TypekernelSkeleton",
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
            "familyName": "TypekernelSkeleton",
            "styleName": "Regular",
            "uniqueFontIdentifier": "typekernel-skeleton",
            "fullName": "Typekernel Skeleton",
            "psName": "TypekernelSkeleton-Regular",
            "version": "0.1",
        }
    )
    out = path.with_suffix(".otf")
    out.parent.mkdir(parents=True, exist_ok=True)
    fb.save(str(out))
    return out


def render_word(
    glyphs: list[ComposedGlyph],
    names: list[str],
    kern,
    *,
    w: int,
    h: int,
    xh_px: float,
) -> Image.Image:
    ctx = glyphs[0].context
    scale = xh_px / ctx.x_height
    px = max(14, round(ctx.units_per_em * scale))
    ss = 3
    otf = bake_otf(glyphs, names, OUT_DIR / f"_tmp_{id(glyphs)}")
    font = ImageFont.truetype(str(otf), size=px * ss)
    xs = [x * scale for x in layout_glyphs(glyphs, names, kerning=kern)]
    content = xs[-1] + glyphs[-1].advance * scale
    x0 = (w - content) / 2
    base = h * 0.68
    img = Image.new("RGB", (w * ss, h * ss), BG)
    d = ImageDraw.Draw(img)
    for ch, x in zip(names, xs, strict=True):
        d.text(((x0 + x) * ss, base * ss), ch, font=font, fill=FG, anchor="ls")
    return img.resize((w, h), Image.Resampling.LANCZOS)


def build_optical_word(ctx: DesignContext) -> tuple[list[ComposedGlyph], object, object]:
    glyphs = build_control_word(WORD, ctx)
    names = list(WORD)
    spaced = space_word_optical(glyphs, names)
    report = word_report(list(spaced.glyphs), names, kerning=spaced.kerning)
    return list(spaced.glyphs), spaced.kerning, report


def build_weight_row() -> list[tuple[str, list[ComposedGlyph], object, object]]:
    """Same skeletons, stem / contrast variants (coding-friendly weights)."""
    base = DesignContext.code_clear()
    variants = [
        ("Light", base.tuned(stem=64.0, contrast=0.92)),
        ("Regular", base),
        ("Bold", base.tuned(stem=108.0, contrast=0.88)),
    ]
    rows = []
    for label, ctx in variants:
        glyphs, kern, report = build_optical_word(ctx)
        rows.append((label, glyphs, kern, report))
    return rows


def build_class_kern_demo(ctx: DesignContext) -> tuple[str, float, float]:
    """Straight/round class kern on skeleton n/o (GENERAL, not face-specific)."""

    from typekernel.parts import skel_c

    n = build_n(ctx)
    glyphs = {
        "n": n,
        "h": h_from_n(n),
        "o": build_o(ctx),
        "c": skel_c(ctx),
    }
    classes = (
        KernClass("straight", ("n", "h")),
        KernClass("round", ("o", "c")),
    )
    rhythm = rhythm_from_control_glyphs(glyphs["n"], glyphs["o"])
    table = auto_class_kern(glyphs, classes, target=rhythm)
    return (
        f"target_gap={rhythm.target_gap:.1f}",
        table.lookup_classes("straight", "round"),
        table.lookup_classes("round", "straight"),
    )


def main() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_IMG.mkdir(parents=True, exist_ok=True)

    panel_w, panel_h = 420, 220
    weight_h = 160
    footer_h = 110
    pad = 24
    title_h = 72
    cols = 3
    total_w = pad * 2 + cols * panel_w + (cols - 1) * 16
    total_h = title_h + panel_h + 28 + weight_h + 24 + footer_h + pad

    canvas = Image.new("RGB", (total_w, total_h), BG)
    draw = ImageDraw.Draw(canvas)
    title = _font(22)
    sub = _font(12)
    tiny = _font(11)

    draw.text(
        (pad, 18),
        "Control glyphs → related forms → optical infra",
        font=title,
        fill=FG,
    )
    draw.text(
        (pad, 46),
        "build_n / build_o → h_from_n · optical spacing · class kern   ·   word “ohio”",
        font=sub,
        fill=SUB,
    )

    # Row 1: paper / coding / print contexts
    reports = []
    for i, (label, blurb, ctx) in enumerate(CONTEXTS):
        glyphs, kern, report = build_optical_word(ctx)
        reports.append((label, report))
        panel = render_word(glyphs, list(WORD), kern, w=panel_w, h=panel_h - 48, xh_px=72)
        x = pad + i * (panel_w + 16)
        y = title_h
        canvas.paste(panel, (x, y + 36))
        draw.text((x, y + 4), label, font=sub, fill=FG)
        draw.text((x, y + 20), blurb, font=tiny, fill=SUB)
        metrics = (
            f"opt ratio {report.optical_gap_ratio:.2f}  ·  stem CV {report.stem_cv:.3f}  ·  "
            f"kinks {report.kink_count}"
        )
        draw.text((x, y + panel_h - 8), metrics, font=tiny, fill=ACCENT)

    # Row 2: weight variants on code_clear skeletons
    y2 = title_h + panel_h + 20
    draw.text((pad, y2), "Stem / contrast variants (same skeletons, code_clear base)", font=sub, fill=FG)
    weights = build_weight_row()
    ww = (total_w - pad * 2 - 32) // 3
    for i, (label, glyphs, kern, report) in enumerate(weights):
        panel = render_word(glyphs, list(WORD), kern, w=ww, h=weight_h - 36, xh_px=56)
        x = pad + i * (ww + 16)
        canvas.paste(panel, (x, y2 + 28))
        stem = glyphs[0].context.stem
        contrast = glyphs[0].context.contrast
        draw.text(
            (x, y2 + weight_h - 4),
            f"{label}  stem={stem:.0f}  contrast={contrast:.2f}  opt={report.optical_gap_ratio:.2f}",
            font=tiny,
            fill=SUB,
        )

    # Footer: class kern numbers
    y3 = y2 + weight_h + 20
    draw.line((pad, y3, total_w - pad, y3), fill=RULE, width=1)
    demo_ctx = DesignContext.geometric_sans()
    note, sr, rs = build_class_kern_demo(demo_ctx)
    draw.text(
        (pad, y3 + 12),
        "Class kern (skeleton n/h vs o/c on geometric_sans):  "
        f"straight→round {sr:.1f} du   ·   round→straight {rs:.1f} du   ·   {note}",
        font=tiny,
        fill=SUB,
    )
    draw.text(
        (pad, y3 + 36),
        "Recipes: parts.skeleton_recipes.build_skel_word(text, ctx) — strokes from x_height / stem / aperture / overshoot; "
        "no branded outlines.",
        font=tiny,
        fill=SUB,
    )
    draw.text(
        (pad, y3 + 56),
        "Infra: control outlines → optics.space_word_optical → auto_class_kern (designer workflow).",
        font=tiny,
        fill=SUB,
    )

    out = DOCS_IMG / NAME
    canvas.save(out, "PNG")
    alt = DOCS_IMG / "control-workflow-specimen.png"
    canvas.save(alt, "PNG")
    (OUT_DIR / NAME).write_bytes(out.read_bytes())
    print(f"wrote {out}")
    for label, report in reports:
        print(
            f"  {label}: opt_ratio={report.optical_gap_ratio:.3f} "
            f"stem_cv={report.stem_cv:.4f} kinks={report.kink_count} "
            f"g1_err={report.g1_join_error_count}"
        )
    return out


if __name__ == "__main__":
    main()
