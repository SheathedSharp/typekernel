"""Three designed masters → one variable font, proofed from the binary.

Weight is not a stroke expand: each master is drawn from its own control
sheet. Heavier masters take thicker stems *and* narrower counters, the way a
designer keeps colour and width in check; the variable font interpolates
between those drawings.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from typekernel.compile import build_variable_font
from typekernel.font import Font, Master
from typekernel.optics.space import space_font
from typekernel.parts import (
    Controls,
    DesignContext,
    auto_class_kern,
    auto_side_kern_classes,
    rhythm_from_control_glyphs,
)

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
DOCS_IMG = HERE.parents[1] / "docs" / "images"

FAMILY = "Typekernel Var"
TEXT = "SPHINX OF QUARTZ 2048 judge my vow"
def master_controls(base: DesignContext, stem: float) -> Controls:
    """A control sheet for one weight: stems change, counters give way."""
    regular = Controls.from_context(base)
    delta = stem - base.stem
    sheet = Controls.from_context(base.tuned(stem=stem))
    return sheet.tuned_n(counter=regular.n.counter - 0.6 * delta).tuned_o(
        rx=regular.o.rx + 0.35 * delta
    )


def master_font(controls: Controls, style: str, weight_class: int) -> Font:
    ctx = controls.context
    drawn = controls.build_all()
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    kerning = auto_class_kern(
        spaced, auto_side_kern_classes(spaced, ctx), target=rhythm
    )
    font = Font.from_context(
        ctx, FAMILY, style, weight_class=weight_class, space_width=spaced["n"].advance * 0.45
    )
    font.add_chars(spaced)
    font.add_class_kern_table(kerning)
    return font


def proof(vf: Path, out: Path) -> Path:
    weights = (200, 300, 400, 500, 600, 700, 800)
    size, margin, label_w = 56, 40, 70
    label_font = ImageFont.load_default(size=16)
    img = Image.new("RGB", (1500, margin * 2 + len(weights) * int(size * 1.35)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    face = ImageFont.truetype(str(vf), size)
    y = margin
    x = margin + label_w
    for w in weights:
        face.set_variation_by_axes([w])
        words = TEXT.split()
        while len(words) > 1 and draw.textlength(" ".join(words), font=face) > img.width - x - margin:
            words.pop()
        draw.text((margin, y + size * 0.4), str(w), font=label_font, fill=(120, 120, 130))
        draw.text((x, y), " ".join(words), font=face, fill=(22, 22, 26), features=["kern"])
        y += int(size * 1.35)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main() -> None:
    base = DesignContext.code_clear()
    masters = [
        Master({"wght": 400}, master_font(master_controls(base, base.stem), "Regular", 400)),
        Master({"wght": 200}, master_font(master_controls(base, 48.0), "Light", 200)),
        Master({"wght": 800}, master_font(master_controls(base, 142.0), "Bold", 800)),
    ]
    result = build_variable_font(masters, OUT_DIR, formats=("ttf", "otf"))
    for fmt, path in result.binaries.items():
        print(f"{fmt}: {path}")
    png = proof(result.binaries["ttf"], OUT_DIR / "proof.png")
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    (DOCS_IMG / "variable-family-proof.png").write_bytes(png.read_bytes())
    print(f"proof: {png}")


if __name__ == "__main__":
    main()
