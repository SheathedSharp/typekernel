"""Evidence gate: pass requires proof hashes + reads_as (E lock)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from typekernel.cli.new import create_project
from typekernel.cli.review_cmd import status_project
from typekernel.project import open_project
from typekernel.review.records import EvidenceRequired, proof_file_hash, record_review


def test_pass_without_proof_refused() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("ev", parent=td, starter="latin-sans")
        with open_project(root) as session, pytest.raises(EvidenceRequired, match="proof"):
            record_review(
                session, "n", verdict="pass", note="ok", reviewer="agent:test"
            )
    finally:
        import shutil

        shutil.rmtree(td)


def test_pass_with_proof_only_refused_without_reads_as() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("ev_reads", parent=td, starter="latin-sans")
        proof = root / "proofs"
        proof.mkdir(exist_ok=True)
        img = proof / "n.png"
        img.write_bytes(b"\x89PNG\r\n\x1afake-proof")
        with open_project(root) as session, pytest.raises(EvidenceRequired, match="reads_as"):
            record_review(
                session,
                "n",
                verdict="pass",
                note="ok",
                reviewer="agent:test",
                proof_paths=[img],
            )
    finally:
        import shutil

        shutil.rmtree(td)


def test_pass_with_proof_and_reads_as_records_and_status_unverified() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("ev2", parent=td, starter="latin-sans")
        proof = root / "proofs"
        proof.mkdir(exist_ok=True)
        img = proof / "n.png"
        img.write_bytes(b"\x89PNG\r\n\x1afake-proof")
        with open_project(root) as session:
            rec = record_review(
                session,
                "n",
                verdict="pass",
                note="ok",
                reviewer="agent:test",
                proof_paths=[img],
                reads_as={"n": "n"},
            )
            assert rec.has_proof_evidence
            assert rec.reads_as == {"n": "n"}
            assert len(rec.proofs) == 1
            assert rec.proofs[0] == proof_file_hash(img)
        text = status_project(root)
        assert "agent-pass (unverified)" in text
        assert "release gate" in text
        assert "blocked" in text
    finally:
        import shutil

        shutil.rmtree(td)


def test_fail_without_proof_still_ok() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("ev3", parent=td, starter="latin-sans")
        with open_project(root) as session:
            rec = record_review(
                session, "n", verdict="fail", note="bad", reviewer="agent:test"
            )
            assert rec.verdict == "fail"
    finally:
        import shutil

        shutil.rmtree(td)
