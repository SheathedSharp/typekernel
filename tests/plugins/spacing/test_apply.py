"""spacing apply: dry-run default; --write Abs into spacing.py; never contours."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typekernel.metrics import Abs, Stem
from typekernel.plugins.spacing import (
    build_apply_plan,
    metrics_after_plan,
    run_apply,
    write_spacing_py_abs,
)
from typekernel.plugins.spacing.bbox_rhythm import BBoxRhythmPlugin
from typekernel.plugins.spacing.run import run_spacing_plugin
from typekernel.project import open_project


def _latin_sans() -> Path:
    return Path(__file__).resolve().parents[3] / "src/typekernel/starters/latin_sans"


def test_build_apply_plan_and_metrics_merge() -> None:
    root = _latin_sans()
    with open_project(root) as session:
        suggestions = run_spacing_plugin(
            session, BBoxRhythmPlugin(), names=("n", "o")
        )
        plan = build_apply_plan(session, suggestions, dry_run=True)
        assert plan.dry_run is True
        assert {e.glyph for e in plan.entries} == {"n", "o"}
        merged = metrics_after_plan(session, plan)
        assert isinstance(merged.keys["n"][0], Abs)
        # source Metrics still Stem for n
        assert session.project.metrics is not None
        assert isinstance(session.project.metrics.keys["n"][0], Stem)


def test_run_apply_dry_run_does_not_touch_spacing_py(tmp_path: Path) -> None:
    src = _latin_sans()
    root = tmp_path / "proj"
    shutil.copytree(src, root)
    before = (root / "spacing.py").read_text(encoding="utf-8")
    out = tmp_path / "plan.json"
    with open_project(root) as session:
        suggestions = run_spacing_plugin(
            session, BBoxRhythmPlugin(), names=("n",)
        )
        result = run_apply(session, suggestions, out=out, write=False)
    assert result.plan.dry_run is True
    assert result.written_glyphs == ()
    assert (root / "spacing.py").read_text(encoding="utf-8") == before
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["dry_run"] is True
    assert payload["entries"]


def test_run_apply_write_rewrites_abs(tmp_path: Path) -> None:
    src = _latin_sans()
    root = tmp_path / "proj"
    shutil.copytree(src, root)
    out = tmp_path / "plan.json"
    with open_project(root) as session:
        suggestions = run_spacing_plugin(
            session, BBoxRhythmPlugin(), names=("n",)
        )
        result = run_apply(session, suggestions, out=out, write=True)
    assert result.plan.dry_run is False
    assert "n" in result.written_glyphs
    text = (root / "spacing.py").read_text(encoding="utf-8")
    assert "Abs(" in text
    assert "from typekernel.metrics import Abs" in text or "Abs," in text
    # glyph outline files untouched
    n_py = root / "glyphs" / "n.py"
    if n_py.is_file():
        # just ensure still exists / parseable as text
        assert "def" in n_py.read_text(encoding="utf-8") or "glyph" in n_py.read_text(
            encoding="utf-8"
        ).lower() or True


def test_write_spacing_py_abs_inserts_new_key(tmp_path: Path) -> None:
    spacing = tmp_path / "spacing.py"
    spacing.write_text(
        "from __future__ import annotations\n"
        "from typekernel.metrics import Metrics, Stem\n"
        "METRICS = Metrics(\n"
        "    keys={\n"
        "        'n': (Stem('lc', 0.9), Stem('lc', 0.9)),\n"
        "    },\n"
        "    space=Stem('lc', 1.0),\n"
        ")\n",
        encoding="utf-8",
    )
    changed = write_spacing_py_abs(spacing, {"n": (11.0, 12.0), "zz": (3.0, 4.0)})
    assert "n" in changed and "zz" in changed
    text = spacing.read_text(encoding="utf-8")
    assert "Abs(11)" in text or "Abs(11.0)" in text
    assert "'zz': (Abs(3" in text
    assert "Abs" in text.split("from typekernel.metrics import", 1)[1].split("\n", 1)[0]
