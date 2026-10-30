"""review stale detection and approved:true refusal."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

from typekernel.cli.new import create_project
from typekernel.cli.review_cmd import status_project
from typekernel.project import open_project
from typekernel.qa.gates import write_approval
from typekernel.review.records import is_stale, record_review


def test_status_shows_unreviewed() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("st", parent=td, starter="latin-sans")
        text = status_project(root)
        assert "release gate" in text
    finally:
        shutil.rmtree(td)


def test_stale_only_touched_group() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project("rv", parent=td, starter="latin-sans")
        with open_project(root) as session:
            proof = root / "n-proof.png"
            proof.write_bytes(b"png-bytes")
            record_review(
                session,
                "n",
                verdict="pass",
                note="ok",
                reviewer="agent:test",
                proof_paths=[proof],
                reads_as={"n": "n"},
            )
            stale, _changed = is_stale(session, "n")
            assert stale is False
        # Change geometry via system token so outline hash moves.
        sys_py = root / "system.py"
        text = sys_py.read_text(encoding="utf-8")
        sys_py.write_text(
            text.replace('"n_width": 430', '"n_width": 480').replace(
                "'n_width': 430", "'n_width': 480"
            ),
            encoding="utf-8",
        )
        # If token form differs, force an append override.
        if "480" not in sys_py.read_text(encoding="utf-8"):
            sys_py.write_text(
                sys_py.read_text(encoding="utf-8")
                + "\n\nsystem = system.tuned(tokens={**dict(system.tokens), 'n_width': 480})\n",
                encoding="utf-8",
            )
        with open_project(root) as session:
            stale, changed = is_stale(session, "n")
            assert stale is True, (stale, changed, session.project.system.tokens.get("n_width"))
            assert "n" in changed
    finally:
        shutil.rmtree(td)


def test_refuses_agent_approved_true() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        path = td / "approvals" / "gate.json"
        with pytest.raises(ValueError, match="refusing approved:true"):
            write_approval(
                path,
                gate="milestone",
                approved=True,
                approver="agent:gpt",
                date="2026-10-29",
            )
        write_approval(
            path,
            gate="milestone",
            approved=True,
            approver="human:zay",
            date="2026-10-29",
        )
        assert path.is_file()
    finally:
        shutil.rmtree(td)
