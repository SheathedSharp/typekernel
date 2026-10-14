"""Regular + ``ital`` axis VF (italic master via ``italic_design``).

``italic_design`` applies construct stem slant (default 10°) plus counter lean.
Upright masters use ``vf_upright_controls`` for ``wght×ital`` segment compatibility (TK-404).
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
from typekernel.parts.italic import italic_design, vf_upright_controls

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
FAMILY = "Typekernel Italic Var"


def master_font(
    controls: Controls,
    style: str,
    weight_class: int,
    kern_classes: tuple,
) -> Font:
    ctx = controls.context
    drawn = controls.build_all()
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    kerning = auto_class_kern(spaced, kern_classes, target=rhythm)
    font = Font.from_context(
        ctx, FAMILY, style, weight_class=weight_class, space_width=spaced["n"].advance * 0.45
    )
    font.add_chars(spaced)
    font.add_class_kern_table(kerning)
    return font


def main() -> None:
    base = DesignContext.code_clear()
    reg = vf_upright_controls(Controls.from_context(base))
    ital = italic_design(reg)
    ref_drawn = reg.build_all()
    ref_rhythm = rhythm_from_control_glyphs(ref_drawn["n"], ref_drawn["o"])
    ref_spaced = space_font(ref_drawn, base, rhythm=ref_rhythm)
    kern_classes = auto_side_kern_classes(ref_spaced, base)
    bold = vf_upright_controls(
        Controls.from_context(base.tuned(stem=120.0)).with_stem_relief()
    )
    bold_ital = italic_design(bold)
    masters = [
        Master({"wght": 400, "ital": 0}, master_font(reg, "Regular", 400, kern_classes)),
        Master({"wght": 400, "ital": 1}, master_font(ital, "Italic", 400, kern_classes)),
        Master({"wght": 700, "ital": 0}, master_font(bold, "Bold", 700, kern_classes)),
        Master(
            {"wght": 700, "ital": 1},
            master_font(bold_ital, "Bold Italic", 700, kern_classes),
        ),
    ]
    result = build_variable_font(masters, OUT_DIR, formats=("ttf",))
    for fmt, path in result.binaries.items():
        print(f"{fmt}: {path}")


if __name__ == "__main__":
    main()
