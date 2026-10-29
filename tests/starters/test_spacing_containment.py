"""Every starter's packed advance must contain its ink.

The italic packing regression was invisible because tests only asserted
``advance > 0``. A slanted cap measured at x-height collapsed to its stem
width and the next glyph landed on the crossbar. This catches any right
overhang across the whole starter charset.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.cli.build import build_font_from_project
from typekernel.cli.load import load_project
from typekernel.cli.new import create_project
from typekernel.geo.outline import bounds

STARTERS = ("latin-sans", "latin-humanist-italic", "latin-chancery")


@pytest.mark.parametrize("starter", STARTERS)
def test_packed_advance_contains_ink(tmp_path: Path, starter: str) -> None:
    root = create_project(f"contain_{starter.replace('-', '_')}", parent=tmp_path, starter=starter)
    project = load_project(root)
    font = build_font_from_project(project, family_name="Contain", project_root=root)

    overhangs: list[tuple[str, float, float]] = []
    for glyph in font:
        if not glyph.outline.contours or not any(c.segments for c in glyph.outline.contours):
            continue
        # Combining marks are zero-advance by design; ink around the attachment
        # point is expected to extend past both sides of the origin.
        if float(glyph.advance) == 0.0:
            continue
        _min_x, _min_y, max_x, _max_y = bounds(glyph.outline)
        if max_x > float(glyph.advance) + 1e-6:
            overhangs.append((glyph.name, float(max_x), float(glyph.advance)))
    assert not overhangs, f"{starter}: ink right of advance: {overhangs}"
