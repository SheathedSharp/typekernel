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
from typekernel.compile.family_build import (
    FamilyBuildOptions,
    compose_font_from_controls,
    reference_kern_classes,
)
from typekernel.compile.features import (
    add_case_punctuation,
    add_fraction_forms,
    add_ordn_forms,
    add_standard_ligatures,
    add_tabular_alternates,
    standard_feature_text,
)
from typekernel.compile.oblique import oblique_font
from typekernel.compile.ufo_export import font_to_ufo, write_font_to_ufo, write_outline_to_ufo
from typekernel.compile.ufo_import import read_font_from_ufo

__all__ = [
    "STRUCTURAL_PROBLEMS",
    "BuildManifest",
    "FamilyBuildOptions",
    "FontBuild",
    "VariableFontBuild",
    "add_case_punctuation",
    "add_ordn_forms",
    "add_fraction_forms",
    "add_standard_ligatures",
    "add_tabular_alternates",
    "build_binary_from_ufo",
    "build_font",
    "build_ttf_from_ufo",
    "build_variable_font",
    "compose_font_from_controls",
    "deep_check_masters",
    "font_to_ufo",
    "oblique_font",
    "read_font_from_ufo",
    "reference_kern_classes",
    "standard_feature_text",
    "write_font_to_ufo",
    "write_masters_designspace",
    "write_outline_to_ufo",
]
