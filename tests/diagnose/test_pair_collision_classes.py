"""PairCollisionCheck expands ClassKernPair via KernClass members."""

from __future__ import annotations

from pathlib import Path

from typekernel.diagnose.engine import audit_project


def test_latin_sans_zero_collision_warns() -> None:
    root = Path(__file__).resolve().parents[2] / "src/typekernel/starters/latin_sans"
    report = audit_project(root)
    coll = [f for f in report.findings if f.check == "spacing.collision"]
    assert coll == [], f"expected 0 collision warns, got {len(coll)}: " + "; ".join(
        f.message for f in coll[:5]
    )
