"""Compile bridge: serialize kernel outlines into UFO / font binaries.

This layer is intentionally thin. It writes what the design layers already
decided — it does not apply optical corrections, remove overlaps, or move
points. Geometry in, UFO or TTF/OTF out, via fontTools / ufoLib2 / fontmake
(or ufo2ft). OpenType table authorship stays with those libraries.
"""

from __future__ import annotations

from typekernel.compile.build import (
    STRUCTURAL_PROBLEMS,
    BuildManifest,
    FontBuild,
    VariableFontBuild,
    build_binary_from_ufo,
    build_font,
    build_ttf_from_ufo,
    build_variable_font,
    deep_check_masters,
    write_masters_designspace,
)
from typekernel.compile.ufo_export import font_to_ufo, write_font_to_ufo, write_outline_to_ufo

__all__ = [
    "STRUCTURAL_PROBLEMS",
    "BuildManifest",
    "FontBuild",
    "VariableFontBuild",
    "build_binary_from_ufo",
    "build_font",
    "build_ttf_from_ufo",
    "build_variable_font",
    "deep_check_masters",
    "font_to_ufo",
    "write_font_to_ufo",
    "write_masters_designspace",
    "write_outline_to_ufo",
]
