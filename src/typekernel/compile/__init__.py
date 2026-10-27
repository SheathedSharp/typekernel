"""Compile bridge: serialize kernel outlines into UFO / font binaries."""

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
from typekernel.compile.oblique import oblique_font
from typekernel.compile.ufo_export import font_to_ufo, write_font_to_ufo, write_outline_to_ufo
from typekernel.compile.ufo_import import read_font_from_ufo

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
    "oblique_font",
    "read_font_from_ufo",
    "write_font_to_ufo",
    "write_masters_designspace",
    "write_outline_to_ufo",
]
