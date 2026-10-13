"""Three designed masters → one variable font, proofed from the binary.

Weight is not a stroke expand: each master is drawn from its own control
sheet. Heavier masters take thicker stems *and* narrower counters, the way a
designer keeps colour and width in check; the variable font interpolates
between those drawings.
"""

from __future__ import annotations

from pathlib import Path

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
from typekernel.qa.proof import proof_weight_ladder

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
DOCS_IMG = HERE.parents[1] / "docs" / "images"

FAMILY = "Typekernel Var"
TEXT = "SPHINX OF QUARTZ 2048 judge my vow"


def master_controls(base: DesignContext, stem: float) -> Controls:
    """A control sheet for one weight: stems change, counters give way."""
    return Controls.from_context(base.tuned(stem=stem)).with_stem_relief()


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
    png = proof_weight_ladder(result.binaries["ttf"], TEXT, OUT_DIR / "proof.png")
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    (DOCS_IMG / "variable-family-proof.png").write_bytes(png.read_bytes())
    print(f"proof: {png}")


if __name__ == "__main__":
    main()
