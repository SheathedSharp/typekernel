"""Decoupling litmus — same synthetic glyphs × three corner configs (§9.10 #28).

Glyph sources must not change when only the Project corner wiring changes.
Uses synthetic names only (no single-letter glyph strings).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from typekernel.plugins.corners import bracketed, slab
from typekernel.project import Project
from typekernel.system import Overshoot, System, Zones


def _system() -> System:
    return System(
        upm=1000,
        zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80.0},
    )


def _write_synthetic_glyphs(glyphs: Path) -> list[Path]:
    """All-line synthetic glyphs with foot corner slots (line–line joins)."""
    glyphs.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []

    stem1 = glyphs / "syn_stem1.py"
    stem1.write_text(
        '''\
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("syn.stem1", group="fixture")
def syn_stem1(system: System):
    s = float(system.stem["lc"])
    h = float(system.zones.x)
    return (
        Writer()
        .start((0.0, 0.0))
        .line((s, 0.0))
        .corner("foot.r", stem=s)
        .line((s, h))
        .corner("top.r", stem=s)
        .line((0.0, h))
        .corner("top.l", stem=s)
        .line((0.0, 0.0))
        .corner("foot.l", stem=s)
        .close()
        .build()
    )
''',
        encoding="utf-8",
    )
    files.append(stem1)

    stem2 = glyphs / "syn_stem2.py"
    stem2.write_text(
        '''\
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("syn.stem2", group="fixture")
def syn_stem2(system: System):
    s = float(system.stem["lc"])
    h = float(system.zones.x)
    gap = s * 1.5
    return (
        Writer()
        .start((0.0, 0.0))
        .line((s, 0.0))
        .corner("foot.l.r", stem=s)
        .line((s, h))
        .line((s + gap, h))
        .line((s + gap, 0.0))
        .corner("foot.r.l", stem=s)
        .line((s + gap + s, 0.0))
        .corner("foot.r.r", stem=s)
        .line((s + gap + s, h))
        .line((0.0, h))
        .line((0.0, 0.0))
        .corner("foot.l.l", stem=s)
        .close()
        .build()
    )
''',
        encoding="utf-8",
    )
    files.append(stem2)

    bar1 = glyphs / "syn_bar1.py"
    bar1.write_text(
        '''\
from typekernel.draw import Writer
from typekernel.project import glyph
from typekernel.system import System


@glyph("syn.bar1", group="fixture")
def syn_bar1(system: System):
    s = float(system.stem["lc"])
    w = s * 4.0
    return (
        Writer()
        .start((0.0, 0.0))
        .line((w, 0.0))
        .corner("foot.r", stem=s)
        .line((w, s))
        .corner("top.r", stem=s)
        .line((0.0, s))
        .corner("top.l", stem=s)
        .line((0.0, 0.0))
        .corner("foot.l", stem=s)
        .close()
        .build()
    )
''',
        encoding="utf-8",
    )
    files.append(bar1)
    return files


def _hash_files(files: list[Path]) -> dict[str, str]:
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}


def _kinds(project: Project, name: str) -> tuple[str, ...]:
    drawing = project.evaluate(name)
    return tuple(type(s).__name__ for s in drawing.contours[0].segments)


def test_three_corner_configs_leave_glyph_sources_unchanged(tmp_path: Path) -> None:
    glyphs = tmp_path / "glyphs"
    files = _write_synthetic_glyphs(glyphs)
    before = _hash_files(files)

    # Empty map ≡ plain (unmatched slots stay sharp). Foot slots only for serifs.
    configs = {
        "plain": {},
        "slab": {"*foot*": slab(length=0.42, thickness=0.18)},
        "bracketed": {"*foot*": bracketed(length=0.42, thickness=0.18)},
    }
    names = ("syn.stem1", "syn.stem2", "syn.bar1")

    results: dict[str, dict[str, tuple[str, ...]]] = {}
    for label, corners in configs.items():
        project = Project(_system(), glyphs, corners=corners, ends={})
        project.discover()
        results[label] = {name: _kinds(project, name) for name in names}

    after = _hash_files(files)
    assert after == before, "glyph sources must not change when corner config changes"

    assert results["plain"]["syn.stem1"] != results["slab"]["syn.stem1"]
    assert results["slab"]["syn.stem1"] != results["bracketed"]["syn.stem1"]
    for label in configs:
        for name in names:
            assert len(results[label][name]) >= 4
