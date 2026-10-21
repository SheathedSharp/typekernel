"""From proportions to an installable font file — the designer's order.

Example compile path (may still call legacy FormSources helpers). Prefer Usage A
parts composition in new faces — see ``.agents/skills/typekernel-font-design/``.
"""

from __future__ import annotations

from pathlib import Path

from typekernel.compile import FamilyBuildOptions, build_font, compose_font
from typekernel.parts import FormSources, DesignContext
from typekernel.qa.proof import proof_labeled_waterfall
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
DOCS_IMG = HERE.parents[1] / "docs" / "images"

FAMILY = "Typekernel First"
PROOF_TEXT = (
    "Ça va? Déjà vu, naïve façade, Ærøskøbing — the quick brown fox jumps over 0123456789."
)
FIRST_FONT_OPTIONS = FamilyBuildOptions(
    liga=True,
    tnum=True,
    case=True,
    extended_latin="æøÆØ",
)


def design(controls: FormSources, family: str = FAMILY):
    return compose_font(
        controls.derive(),
        controls.context,
        family,
        options=FIRST_FONT_OPTIONS,
    )


def main() -> None:
    ctx = DesignContext.code_clear()
    controls = FormSources.from_context(ctx)
    _report, gate_fail = check_sentence_gate(controls, text=AGENT_SENTENCE)
    if gate_fail:
        print("sentence gate (warning):", *gate_fail, sep="\n  ")

    regular = build_font(design(controls), OUT_DIR)
    for fmt, path in regular.binaries.items():
        print(f"{fmt}: {path}")

    wide = controls.tuned_n(counter=controls.n.counter * 1.18)
    variant = build_font(
        design(wide, f"{FAMILY} Wide"),
        OUT_DIR / "variant",
        formats=("otf",),
    )

    png = proof_labeled_waterfall(
        [
            ("from_context", regular.binaries["otf"]),
            ("tuned_n(counter x 1.18)", variant.binaries["otf"]),
        ],
        PROOF_TEXT,
        OUT_DIR / "proof.png",
    )
    DOCS_IMG.mkdir(parents=True, exist_ok=True)
    (DOCS_IMG / "first-font-proof.png").write_bytes(png.read_bytes())
    print(f"proof: {png}")


if __name__ == "__main__":
    main()
