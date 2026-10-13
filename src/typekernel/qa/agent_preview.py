"""Minimal font + PNG proofs for a handful of glyphs (coding agents)."""

from __future__ import annotations

from pathlib import Path

from typekernel.compile import FamilyBuildOptions, build_font, compose_font_from_controls
from typekernel.parts import Controls, DesignContext
from typekernel.qa.proof import proof_charset_grid, proof_context
from typekernel.qa.sentence_gate import AGENT_SENTENCE

__all__ = [
    "DEFAULT_FOCUS_GLYPHS",
    "build_glyph_preview",
    "charset_for_preview",
]

DEFAULT_FOCUS_GLYPHS = "no a e f g t y I B ."


def charset_for_preview(focus: str, sentence: str) -> str:
    letters = "".join(ch for ch in (focus + sentence) if ch.isalpha())
    extra = "".join(
        ch for ch in (focus + sentence) if not ch.isspace() and not ch.isalpha()
    )
    return "".join(dict.fromkeys("no" + letters + extra))


def build_glyph_preview(
    *,
    focus: str = DEFAULT_FOCUS_GLYPHS,
    sentence: str = AGENT_SENTENCE,
    out_dir: str | Path = "out",
    family: str = "Typekernel Agent Preview",
) -> dict[str, Path]:
    """Build OTF + grid/sentence PNGs; return paths."""
    out_dir = Path(out_dir)
    controls = Controls.from_context(DesignContext.code_clear())
    charset = charset_for_preview(focus, sentence)
    liga = all(ch in charset for ch in "fil")
    opts = FamilyBuildOptions(chars=charset, liga=liga)
    font = compose_font_from_controls(controls, family, options=opts)
    result = build_font(font, out_dir, formats=("otf",))
    otf = Path(result.binaries["otf"])
    grid_chars = "".join(c for c in focus if not c.isspace())
    grid = proof_charset_grid(otf, out_dir / "grid.png", chars=grid_chars, size=72, cell=96)
    sent = proof_context(otf, sentence, out_dir / "sentence.png", size=36, width=1600)
    return {"otf": otf, "grid": grid, "sentence": sent}
