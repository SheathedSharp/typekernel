"""Deterministic fixture for plugins.spacing BBoxRhythmPlugin."""

from __future__ import annotations

from pathlib import Path

from typekernel.draw import Writer
from typekernel.optics.context import OpticalContext
from typekernel.plugins.spacing import (
    BBoxRhythmPlugin,
    optical_context_from_system,
    run_spacing_plugin,
    write_spacing_suggestions,
)
from typekernel.project import open_project
from typekernel.system import Overshoot, System, Zones


def _box_outline(*, width: float, height: float = 500.0):
    return (
        Writer()
        .start((0.0, 0.0))
        .line((width, 0.0))
        .line((width, height))
        .line((0.0, height))
        .close()
        .build()
    )


def test_bbox_rhythm_narrow_gets_more_air_than_wide() -> None:
    ctx = OpticalContext(units_per_em=1000.0, x_height=500.0, cap_height=700.0)
    from typekernel.optics.sidebearing import suggest_sidebearings

    narrow = suggest_sidebearings(_box_outline(width=80.0).outline(), ctx)
    wide = suggest_sidebearings(_box_outline(width=600.0).outline(), ctx)
    assert narrow[0] > wide[0]


def test_bbox_rhythm_plugin_on_latin_sans_control_names() -> None:
    root = Path(__file__).resolve().parents[3] / "src/typekernel/starters/latin_sans"
    with open_project(root) as session:
        # control rhythm names only — no hard-coded letters in plugin code;
        # test may name glyphs (tests are out of kernel glyph-literal rule).
        names = ("n", "o", "H", "O")
        suggestions = run_spacing_plugin(
            session, BBoxRhythmPlugin(), names=names
        )
    assert suggestions.pairs == ()
    by = {s.glyph: s for s in suggestions.sidebearings}
    assert set(by) == set(names)
    # Narrower n should get >= air than wide o (rhythm heuristic).
    assert by["n"].lsb >= by["o"].lsb * 0.85
    assert by["n"].method == "bbox_rhythm"


def test_write_spacing_suggestions_json(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3] / "src/typekernel/starters/latin_sans"
    out = tmp_path / "spacing-suggestions.json"
    with open_project(root) as session:
        suggestions = run_spacing_plugin(
            session, BBoxRhythmPlugin(), names=("n", "o")
        )
        path = write_spacing_suggestions(suggestions, out, plugin_id="bbox_rhythm")
    assert path == out
    text = out.read_text(encoding="utf-8")
    assert "not auto-applied" in text.lower() or "Not auto-applied" in text
    assert "bbox_rhythm" in text
    assert '"glyph": "n"' in text


def test_optical_context_from_system_reads_zones() -> None:
    system = System(
        upm=1000,
        zones=Zones(base=0, x=520, cap=700, asc=740, desc=-200),
        overshoot=Overshoot(round=12, pointed=10),
        stem={"lc": 80.0},
    )
    ctx = optical_context_from_system(system)
    assert ctx.x_height == 520.0
    assert ctx.cap_height == 700.0
    assert ctx.units_per_em == 1000.0


def test_spacing_context_type_checks() -> None:
    # Protocol structural: BBoxRhythmPlugin has id + suggest
    plug = BBoxRhythmPlugin()
    assert plug.id == "bbox_rhythm"
    assert callable(plug.suggest)
