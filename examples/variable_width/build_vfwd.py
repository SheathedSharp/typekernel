"""Weight + width variable font (``wght`` × ``wdth``)."""

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

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
FAMILY = "Typekernel Var WD"


def master_controls(base: DesignContext, *, stem: float, wdth: float) -> Controls:
    scale = wdth / 100.0
    ctx = base.tuned(stem=stem)
    sheet = Controls.from_context(ctx).with_stem_relief()
    if abs(scale - 1.0) > 0.01:
        sheet = sheet.tuned_n(counter=sheet.n.counter * scale).tuned_o(
            rx=sheet.o.rx * scale,
            ry=sheet.o.ry * (0.92 + 0.08 * scale),
        )
    return sheet


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
    specs = [
        (200, 75, "Light Condensed", 200),
        (200, 125, "Light Extended", 200),
        (400, 100, "Regular", 400),
        (800, 75, "Bold Condensed", 800),
        (800, 125, "Bold Extended", 800),
    ]
    masters = [
        Master(
            {"wght": wght, "wdth": wdth},
            master_font(master_controls(base, stem=48.0 if wght < 400 else (142.0 if wght > 400 else base.stem), wdth=wdth), style, wc),
        )
        for wght, wdth, style, wc in specs
    ]
    result = build_variable_font(masters, OUT_DIR, formats=("ttf",))
    for fmt, path in result.binaries.items():
        print(f"{fmt}: {path}")
    if result.warnings:
        print("warnings:", *result.warnings[:5], sep="\n  ")


if __name__ == "__main__":
    main()
