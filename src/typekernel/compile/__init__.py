"""Compile bridge: serialize kernel outlines into UFO / font binaries.

This layer is intentionally thin. It writes what the design layers already
decided — it does not apply optical corrections, remove overlaps, or move
points. Geometry in, UFO or TTF/OTF out, via fontTools / ufoLib2 / fontmake
(or ufo2ft). OpenType table authorship stays with those libraries.
"""

from __future__ import annotations

__all__: list[str] = []
