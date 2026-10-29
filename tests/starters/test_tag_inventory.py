"""Inventory noncompliant anatomy tags on the three starters.

Does not fail the build for debt — documents the list so it can be burned down.
Info-level ``tags.grammar`` findings surface the same issues at audit time.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from typekernel.anatomy.tags import is_valid_tag
from typekernel.project import open_project

ROOT = Path(__file__).resolve().parents[2] / "src" / "typekernel" / "starters"
STARTERS = ("latin_sans", "latin_humanist_italic", "latin_chancery")


def _collect_tags(starter: str) -> dict[str, set[str]]:
    """Map glyph name → set of node/slot tags from raw drawings."""
    path = ROOT / starter
    out: dict[str, set[str]] = {}
    with open_project(path) as session:
        for name in sorted(session.specs()):
            draft = session.evaluate(name)
            tags: set[str] = set()
            for group in draft.drawing.nodes:
                for node in group:
                    if node.tag:
                        tags.add(node.tag)
            for slot in draft.drawing.slots:
                if slot.tag:
                    tags.add(slot.tag)
            out[name] = tags
    return out


@pytest.mark.parametrize("starter", STARTERS)
def test_inventory_noncompliant_tags(starter: str) -> None:
    by_glyph = _collect_tags(starter)
    bad: list[tuple[str, str]] = []
    for glyph, tags in by_glyph.items():
        for tag in sorted(tags):
            if not is_valid_tag(tag):
                bad.append((glyph, tag))
    # Always produce a stable sorted report for humans / later phases.
    report_lines = [f"{g}\t{t}" for g, t in bad]
    report = "\n".join(report_lines)
    # Smoke: collection succeeded (starters have glyphs).
    assert by_glyph, f"{starter} produced no glyphs"
    # Debt is expected; assert the inventory is well-formed.
    for glyph, tag in bad:
        assert isinstance(glyph, str) and glyph
        assert isinstance(tag, str) and tag
        assert not is_valid_tag(tag)
    # Keep the report accessible when pytest -s is used.
    if report:
        print(f"\n# noncompliant tags in {starter} ({len(bad)})\n{report}\n")


def test_control_stem_tags_already_legal_on_latin_sans() -> None:
    """H/n stem corners already use the normative stem.*.foot/top.[oi] form."""
    by_glyph = _collect_tags("latin_sans")
    for name in ("H", "n"):
        tags = by_glyph[name]
        stemish = [t for t in tags if t.startswith("stem.")]
        assert stemish, f"{name} missing stem.* tags"
        for t in stemish:
            assert is_valid_tag(t), t
