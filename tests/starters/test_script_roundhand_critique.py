"""script-roundhand: zayju forever young critique + join exits."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.cli.review_cmd import critique_text
from typekernel.diagnose.engine import audit_project
from typekernel.metrics.join import measure_text_joins
from typekernel.project import open_project
from typekernel.review.critique import critique_project

TEXT = "zayju forever young"


def test_roundhand_critique_identity_and_join_on_cold_string(tmp_path: Path) -> None:
    root = create_project("rh_crit", parent=tmp_path, starter="script-roundhand")
    report = critique_project(root, TEXT)
    by = {r.signal: r for r in report.rows}
    assert by["read.identity"].level == "ok"
    assert by["read.identity"].score == 1.0
    assert "read.confuse" not in by
    assert by["join.dy"].level == "ok"
    assert by["join.dy"].score == 1.0
    assert by["join.rhythm_cv"].level == "ok"
    table = critique_text(root, TEXT)
    assert "warns=0" in table
    assert "0 hard warn" in by["read.identity"].detail

    with open_project(root) as session:
        glyphs = {n: session.glyph(n) for n in session.specs()}
        measures, cv = measure_text_joins(glyphs, TEXT, use_join_advance=True)
        joined = [m for m in measures if m.has_join]
        assert len(joined) >= 10
        assert max(m.dy for m in joined) < 20.0
        assert cv <= session.project.metrics.join.max_gap_cv  # type: ignore[union-attr]

    audit = audit_project(root)
    assert audit.errors == []
    assert audit.warnings == []
