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

from typekernel.compile import build_font
from typekernel.compile.features import (
    add_case_punctuation,
    add_standard_ligatures,
    add_tabular_alternates,
    standard_feature_text,
)
from typekernel.font import Font
from typekernel.optics.space import space_font
from typekernel.parts import (
    Controls,
    DesignContext,
    auto_class_kern,
    auto_side_kern_classes,
    rhythm_from_control_glyphs,
)
from typekernel.parts.diacritics import add_composite_latin
from typekernel.qa.proof import proof_labeled_waterfall

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"
DOCS_IMG = HERE.parents[1] / "docs" / "images"

FAMILY = "Typekernel First"
PROOF_TEXT = (
    "Ça va? Déjà vu, naïve façade, Ærøskøbing — the quick brown fox jumps over 0123456789."
)


def design(controls: Controls, family: str = FAMILY) -> Font:
    ctx = controls.context
    drawn = controls.build_all(controls.supported + "æøÆØ")
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)

    classes = auto_side_kern_classes(spaced, ctx)
    kerning = auto_class_kern(spaced, classes, target=rhythm)

    font = Font.from_context(ctx, family, space_width=spaced["n"].advance * 0.45)
    font.add_chars(spaced)
    add_composite_latin(font, controls.control_glyphs())
    add_tabular_alternates(font, spaced)
    add_standard_ligatures(font, controls.control_glyphs())
    add_case_punctuation(font, spaced)
    font.features = standard_feature_text(liga=True, case=True)
    font.add_class_kern_table(kerning)
    return font


def main() -> None:
    ctx = DesignContext.code_clear()
    controls = Controls.from_context(ctx)
    regular = build_font(design(controls), OUT_DIR)
    for fmt, path in regular.binaries.items():
        print(f"{fmt}: {path}")

    # One change on the control sheet: a wider n counter, carried by h m r u.
    wide = controls.tuned_n(counter=controls.n.counter * 1.18)
    variant = build_font(design(wide, f"{FAMILY} Wide"), OUT_DIR / "variant", formats=("otf",))

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
