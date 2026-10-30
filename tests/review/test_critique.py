"""S5 tk critique objective self-score table."""

from __future__ import annotations

import json
from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.cli.review_cmd import critique_text, review_record
from typekernel.review.critique import critique_project


def _strip_expect_changes(root: Path) -> None:
    reviews = root / "reviews"
    if not reviews.is_dir():
        return
    for path in reviews.glob("*-r*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "expect_changes" in data:
            data["expect_changes"] = []
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_critique_on_latin_sans_emits_core_signals(tmp_path: Path) -> None:
    root = create_project("crit_sans", parent=tmp_path, starter="latin-sans")
    report = critique_project(root, "zayju forever young")
    signals = {r.signal for r in report.rows}
    assert "read.identity" in signals
    assert "contour.quality" in signals
    assert "evidence.review" in signals
    assert any(s.startswith("join.") for s in signals)
    table = critique_text(root, "zayju forever young")
    assert "tk critique:" in table
    assert "read.identity" in table
    assert "objective program signals" in table
    payload = json.loads(critique_text(root, "zayju forever young", as_json=True))
    assert payload["text"] == "zayju forever young"
    assert payload["glyphs"] >= 1
    assert any(r["signal"] == "read.identity" for r in payload["rows"])


def test_critique_expect_warns_when_reviews_lack_rationale(tmp_path: Path) -> None:
    root = create_project("crit_expect", parent=tmp_path, starter="latin-sans")
    _strip_expect_changes(root)
    report = critique_project(root, "nnonoo")
    warn = next(r for r in report.rows if r.signal == "expect.changes")
    assert warn.level == "warn"


def test_critique_expect_ok_with_rationale(tmp_path: Path) -> None:
    root = create_project("crit_ok", parent=tmp_path, starter="latin-sans")
    # Starter copy already seeds expect_changes on one review.
    report = critique_project(root, "nnonoo")
    row = next(r for r in report.rows if r.signal == "expect.changes")
    assert row.level == "ok"

    # Also verify CLI record path appends rationales.
    proof = root / "proofs"
    proof.mkdir(exist_ok=True)
    img = proof / "n.png"
    img.write_bytes(b"\x89PNG\r\n\x1afake")
    review_record(
        root,
        "n",
        verdict="pass",
        note="documented",
        reviewer="agent:test",
        proof_paths=[img],
        expect_changes=["agent kept stock topology expects"],
    )
    again = critique_project(root, "nnonoo")
    assert next(r for r in again.rows if r.signal == "expect.changes").level == "ok"
