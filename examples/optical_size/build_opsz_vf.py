"""Text + display masters on the ``opsz`` axis (optical size).

Each master is a designed :class:`~typekernel.parts.context.DesignContext` from
:func:`~typekernel.parts.optical_size.context_for_opsz` — not a scaled outline.
Text (``opsz=14``) is slightly heavier / opener / tighter; display (``opsz=72``)
is lighter / looser / more overshoot. Shared kern classes follow the text master.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from typekernel.compile import build_font, build_variable_font, reference_kern_classes
from typekernel.font import Font, Master
from typekernel.optics.space import space_font
from typekernel.parts import (
    FormSources,
    DesignContext,
    auto_class_kern,
    context_for_opsz,
    rhythm_from_control_glyphs,
)
from typekernel.parts.optical_size import DEFAULT_DISPLAY_OPSZ, DEFAULT_TEXT_OPSZ
from typekernel.qa.proof import proof_axis_ladder, proof_labeled_waterfall
from typekernel.qa.sentence_gate import AGENT_SENTENCE

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
FAMILY = "Typekernel Optical Size"
VF_LADDER_TEXT = "Hamburgevons 0123 — opsz ladder (text → display)."


def master_font(
    controls: FormSources,
    style: str,
    weight_class: int,
    kern_classes: tuple,
) -> Font:
    ctx = controls.context
    # Compose-time stock derivation after locked controls (not a DesignSequence design session).
    drawn = controls.derive()
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    kerning = auto_class_kern(spaced, kern_classes, target=rhythm)
    font = Font.from_context(
        ctx,
        FAMILY,
        style,
        weight_class=weight_class,
        space_width=spaced["n"].advance * 0.45,
    )
    font.add_chars(spaced)
    font.add_class_kern_table(kerning)
    return font


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=OUT_DIR,
        help="Output directory for VF binaries and proofs",
    )
    args = parser.parse_args()
    out_dir = args.out

    base = DesignContext.code_clear()
    text_ctx = context_for_opsz(base, DEFAULT_TEXT_OPSZ)
    display_ctx = context_for_opsz(base, DEFAULT_DISPLAY_OPSZ)
    text = FormSources.from_context(text_ctx)
    display = FormSources.from_context(display_ctx)
    kern_classes = reference_kern_classes(text.derive(), text.context)

    masters = [
        Master(
            {"opsz": DEFAULT_TEXT_OPSZ},
            master_font(text, "Text", 400, kern_classes),
        ),
        Master(
            {"opsz": DEFAULT_DISPLAY_OPSZ},
            master_font(display, "Display", 400, kern_classes),
        ),
    ]
    result = build_variable_font(masters, out_dir, formats=("ttf",))
    for fmt, path in result.binaries.items():
        print(f"{fmt}: {path}")

    ttf = result.binaries["ttf"]
    ladder = proof_axis_ladder(
        ttf,
        VF_LADDER_TEXT,
        out_dir / "proof_vf.png",
        axis_values=(14, 28, 42, 56, 72),
        label_fmt="{:.0f}",
    )
    print(f"proof_vf: {ladder}")

    static_dir = out_dir / "static"
    otfs: list[tuple[str, Path]] = []
    for master in masters:
        label = master.style_name
        built = build_font(
            master.font,
            static_dir / label.lower(),
            formats=("otf",),
        )
        otf = built.binaries["otf"]
        opsz = master.location["opsz"]
        otfs.append((f"{label} opsz={opsz:.0f}", otf))
        print(f"static {label} -> {otf}")
    proof = proof_labeled_waterfall(
        otfs,
        AGENT_SENTENCE,
        out_dir / "proof.png",
        sizes=(28, 48),
    )
    print(f"proof: {proof}")


if __name__ == "__main__":
    main()
