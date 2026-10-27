"""Wire System + glyphs/ into a Project (sans: corners default plain)."""

from __future__ import annotations

import sys
from pathlib import Path

from system import FAMILY_NAME, STYLE_NAME, masters, system

from typekernel.plugins.corners import plain
from typekernel.project import Project

ROOT = Path(__file__).resolve().parent

__all__ = ["FAMILY_NAME", "ROOT", "STYLE_NAME", "get_project"]


def get_project() -> Project:
    root_s = str(ROOT)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    return Project(
        system,
        ROOT / "glyphs",
        masters=masters,
        corners={"*": plain()},
    )
