"""tk audit loads BRIEF/INTENT and reports contradictions (project-level)."""

from __future__ import annotations

from pathlib import Path

from typekernel.cli.audit import audit_project, load_intent
from typekernel.cli.new import create_project
from typekernel.system import Intent


def test_humanist_starter_intent_loads_and_matches(tmp_path: Path) -> None:
    root = create_project("humanist_intent", parent=tmp_path, starter="latin-humanist-italic")
    assert (root / "brief.md").is_file()
    intent = load_intent(root)
    assert intent is not None
    assert intent.contrast == "medium"
    assert intent.slant == "italic"
    report = audit_project(root, glyphs=["n", "o"])
    intent_findings = [f for f in report.findings if f.kind == "intent"]
    assert intent_findings == [], [f.message for f in intent_findings]


def test_audit_warns_when_system_contradicts_intent(tmp_path: Path) -> None:
    root = create_project("drift_intent", parent=tmp_path, starter="latin-humanist-italic")
    system_py = root / "system.py"
    text = system_py.read_text(encoding="utf-8")
    # Force low calligraphic contrast while BRIEF still says medium.
    text = text.replace('"pen_contrast": 0.52', '"pen_contrast": 0.90')
    system_py.write_text(text, encoding="utf-8")
    report = audit_project(root, glyphs=["n"])
    intent_findings = [f for f in report.findings if f.kind == "intent"]
    assert intent_findings
    assert any("contrast" in f.message for f in intent_findings)
    assert all(f.level == "warn" for f in intent_findings)
    assert all(f.glyph == "*" for f in intent_findings)


def test_empty_scaffold_has_brief_stub(tmp_path: Path) -> None:
    root = create_project("empty_brief", parent=tmp_path, starter="empty")
    assert (root / "brief.md").is_file()
    assert load_intent(root) is None  # Intent commented out in empty scaffold
