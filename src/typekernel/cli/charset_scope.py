"""Apply minimal charset scope to a freshly scaffolded project (S0)."""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["apply_minimal_charset"]


def apply_minimal_charset(root: Path, text: str) -> None:
    """Inject / replace charset with ``Charset.from_string(text)`` + minimal mode."""
    project_py = root / "project.py"
    if not project_py.is_file():
        return
    src = project_py.read_text(encoding="utf-8")

    def ensure_charset_import(m: re.Match[str]) -> str:
        names = m.group(1)
        if "Charset" in names:
            return m.group(0)
        return f"from typekernel.project import Charset, {names}"

    src = re.sub(
        r"from typekernel\.project import ([^\n]+)",
        ensure_charset_import,
        src,
        count=1,
    )
    if "PROJECT = Project(" not in src:
        project_py.write_text(src, encoding="utf-8")
        return

    nl = "\n"
    assignment = (
        "_MINIMAL_TEXT = "
        + repr(text)
        + nl
        + "_SCOPE_CHARSET = Charset.from_string(_MINIMAL_TEXT)"
        + nl
        + nl
    )
    if "_SCOPE_CHARSET = Charset.from_string" not in src:
        src = src.replace("PROJECT = Project(", assignment + "PROJECT = Project(", 1)

    # Replace existing charset=... with scope charset, or insert.
    if re.search(r"charset\s*=", src.split("PROJECT = Project(", 1)[1][:1200]):
        src = re.sub(
            r"charset\s*=\s*[^,\n]+",
            "charset=_SCOPE_CHARSET",
            src,
            count=1,
        )
    else:
        src = src.replace(
            "PROJECT = Project(",
            "PROJECT = Project(" + nl + "    charset=_SCOPE_CHARSET,",
            1,
        )

    head = src.split("PROJECT = Project(", 1)[1][:1200]
    if 'charset_mode="minimal"' not in head and "charset_mode='minimal'" not in head:
        src = src.replace(
            "charset=_SCOPE_CHARSET",
            'charset=_SCOPE_CHARSET,' + nl + '    charset_mode="minimal"',
            1,
        )
    project_py.write_text(src, encoding="utf-8")
