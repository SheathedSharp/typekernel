"""S5 expect.changes audit check."""

from __future__ import annotations

import json
from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.cli.review_cmd import review_record
from typekernel.diagnose.engine import audit_project


def _strip_expect_changes(root: Path) -> None:
    reviews = root / "reviews"
    if not reviews.is_dir():
        return
    for path in reviews.glob("*-r*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("expect_changes"):
            data["expect_changes"] = []
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_latin_sans_with_starter_rationale_quiet_on_expect(tmp_path: Path) -> None:
    root = create_project("exp_quiet", parent=tmp_path, starter="latin-sans")
    report = audit_project(root)
    assert not [f for f in report.findings if f.check == "expect.changes"]


def test_expect_warns_when_reviews_lack_rationale(tmp_path: Path) -> None:
    root = create_project("exp_warn", parent=tmp_path, starter="latin-sans")
    _strip_expect_changes(root)
    report = audit_project(root)
    warns = [f for f in report.warnings if f.check == "expect.changes"]
    assert len(warns) == 1


def test_expect_quiet_when_rationale_recorded(tmp_path: Path) -> None:
    root = create_project("exp_ok", parent=tmp_path, starter="latin-sans")
    _strip_expect_changes(root)
    proof = root / "proofs"
    proof.mkdir(exist_ok=True)
    img = proof / "n.png"
    img.write_bytes(b"\x89PNG\r\n\x1afake")
    review_record(
        root,
        "n",
        verdict="pass",
        reviewer="agent:test",
        proof_paths=[img],
        expect_changes=["kept starter topology expects for control glyphs"],
    )
    report = audit_project(root)
    assert not [f for f in report.findings if f.check == "expect.changes"]
