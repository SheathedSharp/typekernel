"""P2-5: B-class topology findings on unmodified latin-sans (appendix A)."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.diagnose import audit_project


def test_appendix_a_b_class_on_latin_sans() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("topo", parent=td, starter="latin-sans")
        report = audit_project(root)
        by_glyph: dict[str, list[str]] = {}
        for f in report.findings:
            if not f.check.startswith("topology."):
                continue
            if f.glyph:
                by_glyph.setdefault(f.glyph, []).append(f.check)

        # A-2 closed in P3-7 (e is open_bowl+BarSpec → 1 counter + 1 aperture).
        assert "topology.counters" not in by_glyph.get("e", []), by_glyph.get("e")
        assert "topology.apertures" not in by_glyph.get("e", []), by_glyph.get("e")
        # A-3: three has ≥2 counters, expect 0
        assert "topology.counters" in by_glyph.get("three", []), by_glyph.get("three")
        # A-6 / B bowl topology: B counters ≠ 2
        assert "topology.counters" in by_glyph.get("B", []), by_glyph.get("B")
        # A-8 partial: five closed when it should be open
        assert "topology.counters" in by_glyph.get("five", []), by_glyph.get("five")
    finally:
        shutil.rmtree(td)


def test_aperture_index_count_unique_n() -> None:
    """topology.apertures counts unique aperture.N, not endpoint tags."""
    from typekernel.anatomy.curves import open_bowl
    from typekernel.diagnose.checks.topology import (
        _aperture_index_count,
        _aperture_tags,
    )

    d = open_bowl((200.0, 260.0), 180.0, 260.0, thick=84.0, thin=70.0, aperture=0.42)
    tags = _aperture_tags(d)
    assert sorted(tags) == ["aperture.0.a", "aperture.0.b"]
    assert _aperture_index_count(tags) == 1
    assert _aperture_index_count(["aperture.0.a", "aperture.0.b", "aperture.1.a"]) == 2
