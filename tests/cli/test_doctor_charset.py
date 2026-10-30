"""S0 doctor + minimal charset scaffolding."""

from __future__ import annotations

import tempfile
from pathlib import Path

from typekernel.cli.audit import audit_project
from typekernel.cli.doctor import check_environment, format_doctor_report
from typekernel.cli.new import create_project
from typekernel.project import open_project
from typekernel.project.scope import scoped_glyph_names


def test_doctor_reports_compile_ok_in_dev_env() -> None:
    report = check_environment()
    text = format_doctor_report(report)
    assert "tk doctor:" in text
    assert "compile:fontTools" in text


def test_minimal_charset_scopes_audit_names() -> None:
    td = Path(tempfile.mkdtemp())
    try:
        root = create_project(
            "mini",
            parent=td,
            starter="latin-sans",
            charset="minimal",
            text="zy",
        )
        with open_project(root) as session:
            assert session.project.charset_mode == "minimal"
            names = scoped_glyph_names(session)
            assert "z" in names
            assert "y" in names
            assert "a" not in names
        report = audit_project(root)
        # Should not explode; glyph count reflects scope.
        assert report.glyphs <= 5
    finally:
        import shutil

        shutil.rmtree(td)
