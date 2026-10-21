"""Proof export (OTF + PNG) from agent-authored glyphs / FormSources sugar.

This module does **not** choose proportions or draw letters. Pass ``FormSources``
you built via ``DesignContext``, ``tuned_*``, ``with_glyph``, etc., or compose
glyphs yourself (Usage A) and call :func:`~typekernel.compile.compose_font`.
"""

from __future__ import annotations

from pathlib import Path

from typekernel.compile import FamilyBuildOptions, build_font, compose_font
from typekernel.parts import FormSources
from typekernel.qa.proof import proof_charset_grid, proof_context

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
    controls: FormSources,
    *,
    family: str,
    focus: str = DEFAULT_FOCUS_GLYPHS,
    sentence: str,
    out_dir: str | Path = "out",
) -> dict[str, Path]:
    """Compile *controls* and write grid + sentence PNGs; return paths."""
    out_dir = Path(out_dir)
    charset = charset_for_preview(focus, sentence)
    liga = all(ch in charset for ch in "fil")
    opts = FamilyBuildOptions(liga=liga)
    font = compose_font(
        controls.derive(charset),
        controls.context,
        family,
        options=opts,
    )
    result = build_font(font, out_dir, formats=("otf",))
    otf = Path(result.binaries["otf"])
    grid_chars = "".join(c for c in focus if not c.isspace())
    grid = proof_charset_grid(otf, out_dir / "grid.png", chars=grid_chars, size=72, cell=96)
    sent = proof_context(otf, sentence, out_dir / "sentence.png", size=36, width=1600)
    return {"otf": otf, "grid": grid, "sentence": sent}
