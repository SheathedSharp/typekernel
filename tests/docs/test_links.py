"""Tracked Markdown must not link to missing or gitignored repo paths."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Markdown links and images: [text](target) / ![alt](target)
_LINK = re.compile(r"!\[[^\]]*\]\(([^)]+)\)|\[[^\]]*\]\(([^)]+)\)")

_SKIP_SCHEMES = ("http://", "https://", "mailto:", "data:")


def _tracked_markdown() -> list[Path]:
    out = subprocess.check_output(
        ["git", "ls-files", "-z", "*.md"],
        cwd=ROOT,
        text=False,
    )
    paths = [ROOT / p.decode() for p in out.split(b"\0") if p]
    return sorted(p for p in paths if p.is_file())


def _link_targets(text: str) -> list[str]:
    targets: list[str] = []
    for m in _LINK.finditer(text):
        raw = m.group(1) or m.group(2) or ""
        target = raw.strip().split()[0].strip("<>") if raw.strip() else ""
        if not target:
            continue
        if target.startswith(_SKIP_SCHEMES) or target.startswith("#"):
            continue
        target = target.split("#", 1)[0]
        if target:
            targets.append(target)
    return targets


def _is_gitignored(path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return False
    proc = subprocess.run(
        ["git", "check-ignore", "-q", str(rel)],
        cwd=ROOT,
        check=False,
    )
    return proc.returncode == 0


@pytest.fixture(scope="module")
def markdown_files() -> list[Path]:
    return _tracked_markdown()


def test_tracked_markdown_internal_links_exist_and_are_not_ignored(
    markdown_files: list[Path],
) -> None:
    violations: list[str] = []
    root = ROOT.resolve()
    for md in markdown_files:
        text = md.read_text(encoding="utf-8")
        for target in _link_targets(text):
            # Skip OS-absolute paths that are not repo-root relative.
            if target.startswith("/") and not (root / target.lstrip("/")).exists():
                continue
            dest = (md.parent / target).resolve()
            try:
                rel_dest = dest.relative_to(root)
            except ValueError:
                violations.append(
                    f"{md.relative_to(ROOT)}: link {target!r} resolves outside repo"
                )
                continue
            if not dest.exists():
                violations.append(
                    f"{md.relative_to(ROOT)}: link {target!r} -> missing {rel_dest}"
                )
                continue
            if _is_gitignored(dest):
                violations.append(
                    f"{md.relative_to(ROOT)}: link {target!r} -> gitignored {rel_dest}"
                )
    assert not violations, "broken or gitignored Markdown links:\n" + "\n".join(
        violations
    )

