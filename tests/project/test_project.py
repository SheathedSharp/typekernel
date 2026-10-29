"""Project / @glyph / Master (Project / @glyph / Master) — synthetic glyph names only."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.draw import (
    CornerFill,
    CornerSite,
    Fragment,
    Writer,
)
from typekernel.geo.point import Point
from typekernel.geo.segment import LineSegment
from typekernel.project import GlyphSpec, Master, Project, glyph
from typekernel.system import Overshoot, System, Zones


def _system(*, stem: float = 80.0, advance_token: float | None = None) -> System:
    tokens = {} if advance_token is None else {"advance": advance_token}
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": stem},
        tokens=tokens,
    )


def _rect_drawing(width: float, height: float):
    return (
        Writer()
        .start((0.0, 0.0))
        .line((width, 0.0))
        .corner("ne")
        .line((width, height))
        .line((0.0, height))
        .close()
        .build()
    )


def _chamfer(site: CornerSite, system: System) -> CornerFill:
    trim = 2.0
    a = site.point_in(trim)
    b = site.point_out(trim)
    return CornerFill(trim_in=trim, trim_out=trim, path=Fragment((LineSegment(a, b),)))


def _write_glyphs(dir_path: Path) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "syn_arch.py").write_text(
        '''\
"""Synthetic arch-like rectangle glyph for Project tests."""
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("syn.arch", group="fixture.stem")
def syn_arch(system: System):
    w = float(system.tokens.get("n_width", 100.0))
    h = float(system.zones.x)
    stem = float(system.stem["lc"])
    # Encode stem into height so master System changes are observable.
    top = h + stem * 0.0  # keep height = x zone; width from token/stem
    width = w + stem * 0.1
    return (
        Writer()
        .start((0.0, 0.0))
        .node("foot.l")
        .line((width, 0.0))
        .corner("ne")
        .line((width, top if top else h))
        .line((0.0, h))
        .close()
        .build()
    )


@syn_arch.master("Black")
def syn_arch_black(system: System):
    # Distinct geometry: fixed wide block.
    return (
        Writer()
        .start((0.0, 0.0))
        .line((200.0, 0.0))
        .line((200.0, 200.0))
        .line((0.0, 200.0))
        .close()
        .build()
    )
''',
        encoding="utf-8",
    )
    (dir_path / "fixture_stem.py").write_text(
        '''\
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("fixture.stem", group="fixture")
def fixture_stem(system: System):
    s = float(system.stem["lc"])
    return (
        Writer()
        .start((0.0, 0.0))
        .line((s, 0.0))
        .line((s, 100.0))
        .line((0.0, 100.0))
        .close()
        .build()
    )
''',
        encoding="utf-8",
    )


def test_discover_collects_synthetic_specs(tmp_path: Path) -> None:
    glyphs = tmp_path / "glyphs"
    _write_glyphs(glyphs)
    project = Project(_system(), glyphs)
    project.discover()
    specs = project.specs()
    assert set(specs) == {"syn.arch", "fixture.stem"}
    assert isinstance(specs["syn.arch"], GlyphSpec)
    assert specs["syn.arch"].group == "fixture.stem"
    assert "Black" in specs["syn.arch"].masters
    assert specs["fixture.stem"].group == "fixture"


def test_evaluate_default_and_master_override(tmp_path: Path) -> None:
    glyphs = tmp_path / "glyphs"
    _write_glyphs(glyphs)
    regular = _system(stem=80.0)
    black_sys = _system(stem=140.0)
    project = Project(
        regular,
        glyphs,
        masters=(Master("Black", black_sys),),
    )
    project.discover()
    d0 = project.evaluate("syn.arch")
    d_black = project.evaluate("syn.arch", master="Black")
    # Default uses regular builder (width depends on stem).
    assert d0.contours[0].segments[0].points[1].x == pytest.approx(100.0 + 8.0)
    # Black override is the fixed 200x200 drawing, not merely a retuned System.
    xs = [p.x for seg in d_black.contours[0].segments for p in seg.points]
    assert max(xs) == pytest.approx(200.0)


def test_evaluate_applies_slots_when_configured(tmp_path: Path) -> None:
    glyphs = tmp_path / "glyphs"
    _write_glyphs(glyphs)
    project = Project(
        _system(),
        glyphs,
        corners={"ne": _chamfer},
        ends={},
    )
    project.discover()
    raw = Project(_system(), glyphs)
    raw.discover()
    before = raw.evaluate("syn.arch")
    after = project.evaluate("syn.arch")
    assert any(s.tag == "ne" for s in before.slots)
    assert all(s.tag != "ne" for s in after.slots)
    assert len(after.contours[0].segments) > len(before.contours[0].segments)


def test_to_glyph_advance_resolution(tmp_path: Path) -> None:
    glyphs = tmp_path / "glyphs"
    _write_glyphs(glyphs)

    # Explicit advance wins.
    p = Project(_system(), glyphs, default_advance=999.0)
    p.discover()
    g = p.to_glyph("fixture.stem", advance=42.0)
    assert g.name == "fixture.stem"
    assert g.advance == 42.0
    assert g.outline.contour_count == 1

    # default_advance next.
    g2 = p.to_glyph("fixture.stem")
    assert g2.advance == 999.0

    # tokens['advance'] when no default_advance.
    p3 = Project(_system(advance_token=321.0), glyphs)
    p3.discover()
    assert p3.to_glyph("fixture.stem").advance == 321.0

    # BBox width fallback (stem=80 → width 80).
    p4 = Project(_system(stem=80.0), glyphs)
    p4.discover()
    assert p4.to_glyph("fixture.stem").advance == pytest.approx(80.0)


def test_specs_and_evaluate_require_discover(tmp_path: Path) -> None:
    p = Project(_system(), tmp_path)
    with pytest.raises(RuntimeError, match="discover"):
        p.specs()
    with pytest.raises(RuntimeError, match="discover"):
        p.evaluate("syn.arch")


def test_glyph_decorator_master_attachment_roundtrip() -> None:
    """@glyph + @fn.master work when a registration target is active."""
    from typekernel.project.registry import registration_target

    bucket: dict[str, GlyphSpec] = {}

    with registration_target(bucket):

        @glyph("syn.roundtrip", group="fixture")
        def build(system: System):
            return _rect_drawing(10, 10)

        @build.master("Light")
        def build_light(system: System):
            return _rect_drawing(5, 5)

    assert "syn.roundtrip" in bucket
    assert "Light" in bucket["syn.roundtrip"].masters
    d = bucket["syn.roundtrip"].masters["Light"](_system())
    assert d.contours[0].segments[0].points[1].x == pytest.approx(5.0)
