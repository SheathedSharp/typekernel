"""``tk read`` — glyph identity top-k + confuse-pair warns (S2)."""

from __future__ import annotations

from pathlib import Path

from typekernel.perceive.read import format_read_report, read_glyph, read_text
from typekernel.project import open_project

__all__ = ["read_project"]


def read_project(
    root: str | Path,
    *,
    text: str | None = None,
    glyph: str | None = None,
    intended: str | None = None,
    as_json: bool = False,
) -> tuple[int, str]:
    """Run identity read; return ``(exit_code, formatted report)``.

    Exit 1 when any hard ``warn`` is present (misread / confuse pair).
    """
    root_path = Path(root).resolve()
    with open_project(root_path) as session:
        if text:
            reports = read_text(session, text)
        elif glyph:
            intended_cp = None
            if intended:
                if len(intended) == 1:
                    intended_cp = ord(intended)
                else:
                    # Allow uniXXXX or decimal
                    s = intended.strip()
                    if s.lower().startswith("uni") and len(s) == 7:
                        intended_cp = int(s[3:], 16)
                    else:
                        intended_cp = int(s, 0)
            reports = [
                read_glyph(session, glyph, intended_cp=intended_cp),
            ]
        else:
            raise ValueError("provide --text or a glyph name")
    body = format_read_report(reports, as_json=as_json)
    hard = any(w.level == "warn" for r in reports for w in r.warnings)
    return (1 if hard else 0), body
