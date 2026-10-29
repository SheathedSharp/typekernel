"""``tk kern suggest`` — propose kern pairs without applying them."""

from __future__ import annotations

from pathlib import Path

from typekernel.metrics.kern_suggest import suggest_kern_pairs, write_suggestions
from typekernel.project import open_project

__all__ = ["kern_suggest"]


def kern_suggest(
    root: str | Path,
    *,
    out: str | Path | None = None,
    master: str | None = None,
    target_gap: float = 24.0,
) -> Path:
    """Write ``kerning-suggestions.json`` under the project (or ``out``)."""
    root_path = Path(root).resolve()
    dest = Path(out) if out is not None else root_path / "kerning-suggestions.json"
    with open_project(root_path) as session:
        suggestions = suggest_kern_pairs(
            session, master=master, target_gap=target_gap
        )
    return write_suggestions(suggestions, dest)
