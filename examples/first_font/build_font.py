"""From proportions to an installable font file — the designer's order.

1. Brief / proportions   → DesignContext
2. Control glyphs        → build_n, build_o
3. Related forms         → h_from_n, u_from_n, i
4. Spacing               → optical sidebearings per glyph
5. Kerning               → class kerning fitted to the n/o rhythm
6. Font                  → Font (names, cmap, metrics, zones, kerning)
7. Build + proof         → OTF/TTF, then a proof rendered from the binary
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from typekernel.compile import build_font
from typekernel.font import Font
from typekernel.optics.space import suggest_sidebearings_optical, with_sidebearings
from typekernel.parts import (
    ComposedGlyph,
    DesignContext,
    KernClass,
    auto_class_kern,
    build_i,
    build_n,
    build_o,
    h_from_n,
    rhythm_from_control_glyphs,
    u_from_n,
)

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
DOCS_IMG = HERE.parents[1] / "docs" / "images"

FAMILY = "Typekernel First"
PROOF_TEXT = "nohu noun union onion hoho ioni unhoh"


def design(ctx: DesignContext) -> Font:
    n = build_n(ctx)
    o = build_o(ctx)
    drawn: dict[str, ComposedGlyph] = {
        "n": n,
        "o": o,
        "h": h_from_n(n),
        "u": u_from_n(n),
        "i": build_i(ctx),
    }
    spaced = {
        ch: with_sidebearings(g, *suggest_sidebearings_optical(g, ctx))
        for ch, g in drawn.items()
    }

    classes = (KernClass("straight", ("n", "h", "i", "u")), KernClass("round", ("o",)))
    rhythm = rhythm_from_control_glyphs(spaced["n"], spaced["o"])
    kerning = auto_class_kern(spaced, classes, target=rhythm)

    font = Font.from_context(ctx, FAMILY, space_width=spaced["n"].advance * 0.45)
    font.add_chars(spaced)
    font.add_class_kern_table(kerning)
    return font


def proof(otf: Path, out: Path) -> Path:
    width, margin = 1600, 48
    sizes = (18, 28, 44, 72, 120)
    label_font = ImageFont.load_default(size=16)
    height = margin * 2 + sum(int(s * 1.5) + 24 for s in sizes)
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = margin
    x = margin + 70
    for size in sizes:
        face = ImageFont.truetype(str(otf), size)
        words = PROOF_TEXT.split()
        while len(words) > 1 and draw.textlength(" ".join(words), font=face) > width - x - margin:
            words.pop()
        draw.text((margin, y), f"{size}px", font=label_font, fill=(120, 120, 130))
        draw.text((x, y), " ".join(words), font=face, fill=(22, 22, 26), features=["kern"])
        y += int(size * 1.5) + 24
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main() -> None:
    ctx = DesignContext.code_clear()
    font = design(ctx)
    result = build_font(font, OUT_DIR)
    for fmt, path in result.binaries.items():
        print(f"{fmt}: {path}")
    png = proof(result.binaries["otf"], OUT_DIR / "proof.png")
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    (DOCS_IMG / "first-font-proof.png").write_bytes(png.read_bytes())
    print(f"proof: {png}")


if __name__ == "__main__":
    main()
