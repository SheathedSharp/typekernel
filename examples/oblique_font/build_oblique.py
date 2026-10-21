"""Regular + oblique static masters (``slnt`` via shear, not true italic)."""

from __future__ import annotations

from pathlib import Path

from typekernel.compile import build_font
from typekernel.compile.oblique import oblique_font
from typekernel.font import Font
from typekernel.optics.space import space_font
from typekernel.parts import (
    FormSources,
    DesignContext,
    auto_class_kern,
    auto_side_kern_classes,
    rhythm_from_control_glyphs,
)

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "out"


def design(controls: FormSources, family: str, style: str) -> Font:
    ctx = controls.context
    # Compose-time stock derivation after locked controls (not a DesignSequence design session).
    drawn = controls.derive()
    rhythm = rhythm_from_control_glyphs(drawn["n"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    kerning = auto_class_kern(spaced, auto_side_kern_classes(spaced, ctx), target=rhythm)
    font = Font.from_context(ctx, family, style, space_width=spaced["n"].advance * 0.45)
    font.add_chars(spaced)
    font.add_class_kern_table(kerning)
    return font


def main() -> None:
    ctx = DesignContext.code_clear()
    controls = FormSources.from_context(ctx)
    regular = design(controls, "Typekernel Oblique Demo", "Regular")
    build_font(regular, OUT_DIR / "regular")
    oblique = oblique_font(regular, 12.0, style_name="Oblique")
    build_font(oblique, OUT_DIR / "oblique")
    print(f"wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
