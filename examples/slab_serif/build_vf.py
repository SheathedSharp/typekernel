"""Four slab masters (TK-306 VF) → one ``wght`` variable font + proof.

Stems match ``test_slab_serif_masters_on_vf_stable_charset``: 70 / 100 / 140 / 180
at wght 300 / 400 / 600 / 700. Each master is drawn, not stroke-expanded.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from design import FAMILY_NAME, _voice, baseline_controls

from typekernel.compile import build_variable_font, reference_kern_classes
from typekernel.font import Font, Master, check_masters
from typekernel.optics.space import space_font
from typekernel.parts import Controls, auto_class_kern, rhythm_from_control_glyphs
from typekernel.qa.proof import proof_weight_ladder

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
TEXT = "Slab nHIL GQjt — the quick brown fox jumps over 0123456789."


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
        ctx,
        FAMILY_NAME,
        style,
        weight_class=weight_class,
        space_width=spaced["n"].advance * 0.45,
    )
    font.add_chars(spaced)
    font.add_class_kern_table(kerning)
    return font


def slab_masters(kern_classes: tuple) -> list[Master]:
    """Same stems as VF charset test; ``_voice`` matches static ``build_family``."""
    ladder = (
        (70.0, "Light", 300, False),
        (100.0, "Regular", 400, False),
        (140.0, "Semibold", 600, False),
        (180.0, "Bold", 700, True),
    )
    return [
        Master(
            {"wght": float(wght)},
            master_font(_voice(stem, relief=relief), style, wght, kern_classes),
        )
        for stem, style, wght, relief in ladder
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build slab serif wght VF.")
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    ref = baseline_controls()
    kern_classes = reference_kern_classes(ref)
    masters = slab_masters(kern_classes)
    topo = check_masters(masters)
    if topo:
        print("check_masters:", *topo, sep="\n  ")
        return 1

    result = build_variable_font(masters, out, formats=("ttf", "otf"))
    for fmt, path in result.binaries.items():
        print(f"{fmt}: {path}")
    png = proof_weight_ladder(result.binaries["ttf"], TEXT, out / "proof_vf.png")
    print(f"proof: {png}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
