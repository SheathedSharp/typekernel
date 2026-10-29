"""JSON sidecars next to perceive PNGs (target §6.2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = ["write_sidecar"]


def write_sidecar(png_path: Path | str, payload: dict[str, Any]) -> Path:
    """Write ``payload`` beside ``png_path`` as ``<stem>.json``."""
    path = Path(png_path)
    side = path.with_suffix(".json")
    side.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return side
