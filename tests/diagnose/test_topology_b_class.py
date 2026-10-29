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

        # A-2: e has 2 counters, expect 1
        assert "topology.counters" in by_glyph.get("e", []), by_glyph.get("e")
        # A-3: three has ≥2 counters, expect 0
        assert "topology.counters" in by_glyph.get("three", []), by_glyph.get("three")
        # A-6 / B bowl topology: B counters ≠ 2
        assert "topology.counters" in by_glyph.get("B", []), by_glyph.get("B")
        # A-8 partial: five closed when it should be open
        assert "topology.counters" in by_glyph.get("five", []), by_glyph.get("five")
    finally:
        shutil.rmtree(td)
