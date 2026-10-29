"""tk see edit/context/masters + sidecar + budget."""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.cli.see_cmd import see_project


def test_see_edit_and_context_under_budget() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("see_trial", parent=td, starter="latin-sans")
        out = root / "proofs" / "see"
        # Warm
        see_project(root, "n", out_dir=out, context=True, masters=True, size=256)
        t0 = time.perf_counter()
        paths = see_project(root, "n", out_dir=out, context=True, masters=True, size=256)
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"tk see n --masters --context took {elapsed:.2f}s"
        assert any(p.name == "see-n.png" for p in paths)
        side = out / "see-n.json"
        assert side.is_file()
        meta = json.loads(side.read_text(encoding="utf-8"))
        assert meta["view"] == "edit"
        assert "nodes" in meta
        assert "Measure" in meta or "measures" in meta
        assert "labels" in meta
        # Shoulder / x-height nodes should be labelled so the shoulder check is visible.
        labels = meta.get("labels") or [n.get("tag") for n in meta.get("nodes", [])]
        assert any(labels), "edit view JSON should list node labels"
    finally:
        shutil.rmtree(td)
