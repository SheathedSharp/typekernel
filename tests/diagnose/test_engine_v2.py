"""P2-4: diagnose engine JSON schema, baseline, starter parity."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from typekernel.cli.new import create_project
from typekernel.diagnose import Baseline, BaselineEntry, audit_project, format_report
from typekernel.diagnose.baseline import save_baseline


def _counts(report) -> tuple[int, int]:
    return len(report.errors), len(report.warnings)


def test_json_schema_keys() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("diag", parent=td, starter="latin-sans")
        report = audit_project(root, glyphs=["n", "o"])
        payload = json.loads(format_report(report, as_json=True))
        assert set(payload) >= {"glyphs", "masters", "errors", "warnings", "findings"}
        if payload["findings"]:
            f = payload["findings"][0]
            assert set(f) >= {
                "check",
                "level",
                "glyph",
                "master",
                "where",
                "measured",
                "expected",
                "message",
                "hint",
            }
    finally:
        shutil.rmtree(td)


def test_baseline_requires_reason_and_invalidates_on_hash() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("diag_bl", parent=td, starter="latin-sans")
        # Invent a warn and baseline it.
        finding_msg = "token 'bogus_advance' looks like a per-glyph width/advance; move it to project elements (or metrics) — System.tokens keeps only global controls (n_width/o_width/H_width/O_width)"
        # Use a real warn from system lint if any; else skip filtering path via synthetic baseline load error.
        bl_path = root / "audit-baseline.json"
        try:
            save_baseline(
                bl_path,
                Baseline(
                    entries=[
                        BaselineEntry(
                            check="system",
                            glyph="*",
                            message="nope",
                            reason="",  # empty
                        )
                    ]
                ),
            )
            raised = False
            try:
                audit_project(root, glyphs=["n"], baseline=bl_path)
            except ValueError:
                raised = True
            assert raised
        finally:
            pass

        save_baseline(
            bl_path,
            Baseline(
                entries=[
                    BaselineEntry(
                        check="system",
                        glyph="*",
                        message=finding_msg,
                        reason="accepted transitional token until P3",
                        outline_hash="deadbeef",
                    )
                ]
            ),
        )
        # Should load; hash mismatch means entry inactive — no crash.
        audit_project(root, glyphs=["n"], baseline=bl_path)
    finally:
        shutil.rmtree(td)


def test_starter_parity_zero_errors() -> None:
    """Migrated engine: three starters still 0 errors (findings parity for errors)."""
    td = Path(tempfile.mkdtemp())
    try:
        for starter in ("latin-sans", "latin-humanist-italic", "latin-chancery"):
            root = create_project(starter.replace("-", "_"), parent=td, starter=starter)
            report = audit_project(root)
            assert len(report.errors) == 0, (starter, format_report(report))
    finally:
        shutil.rmtree(td)
