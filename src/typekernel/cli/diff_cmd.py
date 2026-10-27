"""``tk diff`` — which glyphs changed (ARCHITECTURE.md §3.3 / outline_hash).

Compares live project glyph hashes to a JSON snapshot or another project.
Not a golden gate: hashes exist only for change detection.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typekernel.cli.load import load_project
from typekernel.qa.outline_hash import glyph_hash

__all__ = [
    "DEFAULT_SNAPSHOT_NAME",
    "diff_hash_maps",
    "diff_project",
    "format_diff",
    "project_glyph_hashes",
    "write_snapshot",
]

DEFAULT_SNAPSHOT_NAME = "glyph_hashes.json"


def project_glyph_hashes(root: str | Path, *, master: str | None = None) -> dict[str, str]:
    """Evaluate every registered glyph and return ``{name: glyph_hash}``."""
    project = load_project(root)
    project.discover()
    out: dict[str, str] = {}
    for name in sorted(project.specs()):
        out[name] = glyph_hash(project.to_glyph(name, master=master))
    return out


def write_snapshot(root: str | Path, path: str | Path, *, master: str | None = None) -> Path:
    """Write glyph hashes JSON under ``path``; return that path."""
    hashes = project_glyph_hashes(root, master=master)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "kind": "typekernel.glyph_hashes",
        "version": 1,
        "master": master,
        "glyphs": hashes,
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def _load_snapshot(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "glyphs" in data:
        glyphs = data["glyphs"]
    elif isinstance(data, dict):
        glyphs = data
    else:
        raise ValueError(f"snapshot must be a JSON object: {path}")
    if not isinstance(glyphs, dict):
        raise ValueError(f"snapshot glyphs must be an object: {path}")
    return {str(k): str(v) for k, v in glyphs.items()}


def diff_hash_maps(
    before: dict[str, str], after: dict[str, str]
) -> dict[str, list[str]]:
    """Return ``added`` / ``removed`` / ``changed`` glyph name lists."""
    b_keys = set(before)
    a_keys = set(after)
    added = sorted(a_keys - b_keys)
    removed = sorted(b_keys - a_keys)
    changed = sorted(n for n in (a_keys & b_keys) if before[n] != after[n])
    return {"added": added, "removed": removed, "changed": changed}


def diff_project(
    root: str | Path,
    *,
    against: str | Path | None = None,
    master: str | None = None,
) -> dict[str, list[str]]:
    """Diff live ``root`` against a snapshot JSON or another project directory.

    Default ``against`` is ``<root>/build/glyph_hashes.json``.
    """
    root_path = Path(root).resolve()
    after = project_glyph_hashes(root_path, master=master)
    if against is None:
        against_path = root_path / "build" / DEFAULT_SNAPSHOT_NAME
    else:
        against_path = Path(against).resolve()
    if not against_path.exists():
        raise FileNotFoundError(
            f"no baseline at {against_path}; run: tk diff --snapshot {against_path}"
        )
    if against_path.is_dir():
        before = project_glyph_hashes(against_path, master=master)
    else:
        before = _load_snapshot(against_path)
    return diff_hash_maps(before, after)


def format_diff(result: dict[str, list[str]]) -> str:
    """Human-readable summary for CLI stdout."""
    lines = [
        f"tk diff: {len(result['changed'])} changed, "
        f"{len(result['added'])} added, {len(result['removed'])} removed"
    ]
    for label in ("changed", "added", "removed"):
        names = result[label]
        if not names:
            continue
        lines.append(f"  {label}:")
        for name in names:
            lines.append(f"    {name}")
    return "\n".join(lines)
