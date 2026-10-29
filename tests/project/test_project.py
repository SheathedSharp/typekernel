"""ProjectSession / @glyph / MasterSpec — synthetic glyph names only."""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.draw import CornerFill, CornerSite, Fragment, Writer
from typekernel.geo.segment import LineSegment
from typekernel.project import GlyphSpec, glyph, open_project
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


def _write_minimal_project(
    root: Path,
    *,
    stem: float = 80.0,
    advance_token: float | None = None,
    corners: bool = False,
    black_master: bool = False,
) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    glyphs = root / "glyphs"
    glyphs.mkdir(exist_ok=True)
    tokens = ""
    if advance_token is not None:
        tokens = f', tokens={{"advance": {advance_token}}}'
    masters_proj = "masters=(),"
    if black_master:
        # inline won't work - write proper system
        masters_proj = (
            "masters=(MasterSpec('Black', {'wght': 700.0}, "
            "system.tuned(stem={'lc': 140.0})),),"
        )
    corners_import = ""
    corners_arg = "corners=None,"
    if corners:
        corners_import = "from typekernel.plugins.corners import plain\n"
        # use chamfer via a small local filler written into project.py
        corners_arg = "corners={'ne': _chamfer},"
        corners_import = (
            "from typekernel.draw import CornerFill, Fragment\n"
            "from typekernel.geo.segment import LineSegment\n"
            "def _chamfer(site, system):\n"
            "    trim = 2.0\n"
            "    a = site.point_in(trim)\n"
            "    b = site.point_out(trim)\n"
            "    return CornerFill(trim_in=trim, trim_out=trim, "
            "path=Fragment((LineSegment(a, b),)))\n"
        )

    (root / "system.py").write_text(
        "from typekernel.system import Overshoot, System, Zones\n"
        f"system = System(upm=1000, zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200), "
        f"overshoot=Overshoot(round=12, pointed=10), stem={{'lc': {stem}}}{tokens})\n",
        encoding="utf-8",
    )
    (root / "project.py").write_text(
        "from system import system\n"
        "from typekernel.axes import MasterSpec\n"
        "from typekernel.project import FamilyInfo, Project\n"
        f"{corners_import}"
        "PROJECT = Project(\n"
        "    info=FamilyInfo(family='Test'),\n"
        "    system=system,\n"
        "    glyphs='glyphs',\n"
        f"    {masters_proj}\n"
        f"    {corners_arg}\n"
        ")\n",
        encoding="utf-8",
    )
    (glyphs / "syn_arch.py").write_text(
        '''\
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("syn.arch", group="fixture.stem")
def syn_arch(system: System):
    w = float(system.tokens.get("n_width", 100.0))
    h = float(system.zones.x)
    stem = float(system.stem["lc"])
    width = w + stem * 0.1
    return (
        Writer()
        .start((0.0, 0.0))
        .node("foot.l")
        .line((width, 0.0))
        .corner("ne")
        .line((width, h))
        .line((0.0, h))
        .close()
        .build()
    )


@syn_arch.master("Black")
def syn_arch_black(system: System):
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
    (glyphs / "fixture_stem.py").write_text(
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
    return root


def test_discover_collects_synthetic_specs(tmp_path: Path) -> None:
    root = _write_minimal_project(tmp_path / "proj")
    with open_project(root) as session:
        specs = session.specs()
        assert set(specs) == {"syn.arch", "fixture.stem"}
        assert isinstance(specs["syn.arch"], GlyphSpec)
        assert specs["syn.arch"].group == "fixture.stem"
        assert "Black" in specs["syn.arch"].masters
        assert specs["fixture.stem"].group == "fixture"


def test_evaluate_default_and_master_override(tmp_path: Path) -> None:
    root = _write_minimal_project(tmp_path / "proj", stem=80.0, black_master=True)
    with open_project(root) as session:
        d0 = session.evaluate("syn.arch").drawing
        d_black = session.evaluate("syn.arch", master="Black").drawing
        assert d0.contours[0].segments[0].points[1].x == pytest.approx(100.0 + 8.0)
        xs = [p.x for seg in d_black.contours[0].segments for p in seg.points]
        assert max(xs) == pytest.approx(200.0)


def test_evaluate_applies_slots_when_configured(tmp_path: Path) -> None:
    root = _write_minimal_project(tmp_path / "proj", corners=True)
    with open_project(root) as session:
        before = session.evaluate("syn.arch", slots=False).drawing
        after = session.evaluate("syn.arch", slots=True).drawing
        assert any(s.tag == "ne" for s in before.slots)
        assert all(s.tag != "ne" for s in after.slots)
        assert len(after.contours[0].segments) > len(before.contours[0].segments)


def test_glyph_advance_resolution(tmp_path: Path) -> None:
    root = _write_minimal_project(tmp_path / "proj1")
    with open_project(root) as session:
        g = session.glyph("fixture.stem")
        # stem=80 → bbox advance 80 when no token
        assert g.advance == pytest.approx(80.0)

    root2 = _write_minimal_project(tmp_path / "proj2", advance_token=321.0)
    with open_project(root2) as session:
        assert session.glyph("fixture.stem").advance == 321.0


def test_glyph_decorator_master_attachment_roundtrip() -> None:
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
