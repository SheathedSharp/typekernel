"""Compile bridge: serialize kernel outlines into UFO / font binaries.

This layer is intentionally thin. It writes what the design layers already
decided — it does not apply optical corrections, remove overlaps, or move
points. Geometry in, UFO or TTF/OTF out, via fontTools / ufoLib2 / fontmake
(or ufo2ft). OpenType table authorship stays with those libraries.
"""

from __future__ import annotations

from typekernel.compile.build import BuildManifest, build_ttf_from_ufo
from typekernel.compile.ufo_export import write_outline_to_ufo

__all__ = [
    "BuildManifest",
    "build_ttf_from_ufo",
    "write_outline_to_ufo",
]
