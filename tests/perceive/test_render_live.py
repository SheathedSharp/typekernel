"""P2-1: live renderer fill-rule contrast, layout, and budget."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PIL import Image, ImageChops, ImageDraw

from typekernel.font.glyph import Glyph
from typekernel.geo.contour import Contour
from typekernel.geo.outline import Outline
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.perceive.render import (
    LiveGlyph,
    flatten_outline,
    render_live,
    simplify_outline,
)


def _rect(x0: float, y0: float, x1: float, y1: float, *, ccw: bool = True) -> Contour:
    if ccw:
        segs = (
            LineSegment(Point(x0, y0), Point(x1, y0)),
            LineSegment(Point(x1, y0), Point(x1, y1)),
            LineSegment(Point(x1, y1), Point(x0, y1)),
            LineSegment(Point(x0, y1), Point(x0, y0)),
        )
    else:
        segs = (
            LineSegment(Point(x0, y0), Point(x0, y1)),
            LineSegment(Point(x0, y1), Point(x1, y1)),
            LineSegment(Point(x1, y1), Point(x1, y0)),
            LineSegment(Point(x1, y0), Point(x0, y0)),
        )
    return Contour(segs, closed=True)


def _ring_plus_bar() -> Outline:
    """Closed ring with a through-bar (θ-like); nonzero ≠ evenodd."""
    outer = _rect(0, 0, 100, 100, ccw=True)
    hole = _rect(20, 20, 80, 80, ccw=False)
    bar = _rect(10, 45, 90, 55, ccw=True)
    return Outline((outer, hole, bar))


def _ink_count(img: Image.Image) -> int:
    data = img.get_flattened_data()
    return sum(1 for p in data if (p[0] if isinstance(p, tuple) else p) < 200)


def test_nonzero_differs_from_evenodd() -> None:
    outline = _ring_plus_bar()
    nz = render_live([outline], size=128, fill_rule="nonzero", supersample=1)
    eo = render_live([outline], size=128, fill_rule="evenodd", supersample=1)
    assert isinstance(nz, Image.Image) and isinstance(eo, Image.Image)
    diff = ImageChops.difference(nz.convert("RGB"), eo.convert("RGB"))
    changed = sum(1 for p in diff.get_flattened_data() if p != (0, 0, 0))
    assert changed > 50, f"expected fill-rule contrast, got {changed} changed pixels"


def test_single_glyph_under_100ms() -> None:
    outline = _ring_plus_bar()
    render_live([outline], size=256)  # warm
    t0 = time.perf_counter()
    render_live([outline], size=256)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 100.0, f"render_live 256px took {elapsed_ms:.1f} ms"


def test_multi_glyph_advance_and_kerning() -> None:
    box = Outline((_rect(10, 0, 40, 50),))
    left = LiveGlyph(box, advance=60.0)
    right = LiveGlyph(box, advance=60.0)
    tight = render_live([left, right], size=128, kerning=(-20.0,), supersample=1)
    loose = render_live([left, right], size=128, kerning=(40.0,), supersample=1)
    assert isinstance(tight, Image.Image) and isinstance(loose, Image.Image)
    assert list(tight.get_flattened_data()) != list(loose.get_flattened_data())


def test_accepts_glyph_type() -> None:
    outline = Outline((_rect(0, 0, 50, 50),))
    g = Glyph(name="box", outline=outline, advance=60.0)
    img = render_live([g], size=64, supersample=1)
    assert isinstance(img, Image.Image)
    assert _ink_count(img) > 10


def test_live_close_to_freetype(tmp_path: Path) -> None:
    """UPM-aligned live raster vs FreeType: pixel delta < 1%."""
    ufoLib2 = pytest.importorskip("ufoLib2")
    pytest.importorskip("ufo2ft")
    from ufo2ft import compileTTF

    from typekernel.compile.ufo_export import write_outline_to_ufo

    outline = Outline((_rect(100, 100, 500, 700),))
    upm = 1000
    ufo_path = tmp_path / "Live.ufo"
    write_outline_to_ufo(
        outline, ufo_path, glyph_name="A", advance_width=600, units_per_em=upm
    )
    tt = compileTTF(ufoLib2.Font.open(ufo_path))
    ttf_path = tmp_path / "Live.ttf"
    tt.save(str(ttf_path))

    size = 200
    scale = size / upm

    # Live: same UPM framing as FreeType (design y=upm → pixel 0).
    live = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(live)
    for poly in flatten_outline(simplify_outline(outline), chord_budget=0.5):
        pix = [(x * scale, (upm - y) * scale) for x, y in poly]
        if len(pix) >= 3:
            draw.polygon(pix, fill=255)

    from PIL import ImageFont

    face = ImageFont.truetype(str(ttf_path), size=size)
    ft = Image.new("L", (size, size), 0)
    ImageDraw.Draw(ft).text((0, size), "A", font=face, fill=255, anchor="ls")

    diff = ImageChops.difference(live, ft)
    changed = sum(1 for p in diff.get_flattened_data() if p)
    ratio = changed / (size * size)
    assert ratio < 0.01, f"live vs FreeType pixel delta {ratio:.2%} ({changed})"
