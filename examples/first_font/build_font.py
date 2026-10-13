"""From proportions to an installable font file — the designer's order.

1. Brief / proportions   → DesignContext
2. Control glyphs        → Controls (the n and o design records)
3. Related forms         → Controls.build_all(): a–z from n / o; A–Z, 0–9 from H / O
4. Spacing               → optical sidebearings per glyph; tabular figures
5. Kerning               → class kerning fitted to the n/o rhythm
6. Font                  → Font (names, cmap, metrics, zones, anchors, kerning)
7. Build + proof         → OTF/TTF, then a proof rendered from the binary
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from typekernel.compile import build_font
from typekernel.font import Font
from typekernel.optics.space import suggest_sidebearings_optical, with_sidebearings
from typekernel.parts import (
    Controls,
    DesignContext,
    KernClass,
    auto_class_kern,
    rhythm_from_control_glyphs,
    tabular,
)

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
DOCS_IMG = HERE.parents[1] / "docs" / "images"

FAMILY = "Typekernel First"
PROOF_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "Wait — really? Yes: 0123456789; (quotes) \"hello\" and 'world'!"
)


def design(controls: Controls, family: str = FAMILY) -> Font:
    ctx = controls.context
    drawn = controls.build_all()
    spaced = {
        ch: with_sidebearings(g, *suggest_sidebearings_optical(g, ctx))
        for ch, g in drawn.items()
    }
    spaced.update(tabular({ch: g for ch, g in spaced.items() if ch.isdigit()}))

    classes = (
        KernClass("straight", ("n", "h", "m", "i", "l", "u")),
        KernClass("round", ("o",)),
        KernClass("straight_caps", ("H", "I", "M", "N", "U")),
        KernClass("round_caps", ("O", "C", "G", "Q")),
    )
    rhythm = rhythm_from_control_glyphs(spaced["n"], spaced["o"])
    kerning = auto_class_kern(spaced, classes, target=rhythm)

    font = Font.from_context(ctx, family, space_width=spaced["n"].advance * 0.45)
    font.add_chars(spaced)
    font.add_class_kern_table(kerning)
    return font


def proof(rows: list[tuple[str, Path]], out: Path) -> Path:
    width, margin, label_w = 1600, 48, 220
    sizes = (20, 36, 72)
    label_font = ImageFont.load_default(size=16)
    row_h = sum(int(s * 1.5) + 16 for s in sizes) + 24
    img = Image.new("RGB", (width, margin * 2 + row_h * len(rows)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = margin
    x = margin + label_w
    for label, binary in rows:
        draw.text((margin, y), label, font=label_font, fill=(120, 120, 130))
        for size in sizes:
            face = ImageFont.truetype(str(binary), size)
            words = PROOF_TEXT.split()
            while len(words) > 1 and draw.textlength(" ".join(words), font=face) > width - x - margin:
                words.pop()
            draw.text((x, y), " ".join(words), font=face, fill=(22, 22, 26), features=["kern"])
            y += int(size * 1.5) + 16
        y += 24
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main() -> None:
    ctx = DesignContext.code_clear()
    controls = Controls.from_context(ctx)
    regular = build_font(design(controls), OUT_DIR)
    for fmt, path in regular.binaries.items():
        print(f"{fmt}: {path}")

    # One change on the control sheet: a wider n counter, carried by h m r u.
    wide = controls.tuned_n(counter=controls.n.counter * 1.18)
    variant = build_font(design(wide, f"{FAMILY} Wide"), OUT_DIR / "variant", formats=("otf",))

    png = proof(
        [
            ("from_context", regular.binaries["otf"]),
            ("tuned_n(counter x 1.18)", variant.binaries["otf"]),
        ],
        OUT_DIR / "proof.png",
    )
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    (DOCS_IMG / "first-font-proof.png").write_bytes(png.read_bytes())
    print(f"proof: {png}")


if __name__ == "__main__":
    main()
