"""``tk new`` — scaffold an empty typekernel project or copy a starter."""

from __future__ import annotations

import shutil
from pathlib import Path

__all__ = ["STARTERS", "create_project"]

# Starter directory name under typekernel/starters/ → CLI --starter value.
STARTERS: dict[str, str] = {
    "latin-sans": "latin_sans",
}

_SYSTEM_PY = '''\
"""Designer numeric table for this project."""

from __future__ import annotations

from typekernel.system import Overshoot, System, Zones

system = System(
    upm=1000,
    zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
    overshoot=Overshoot(round=12, pointed=10),
    stem={"lc": 80, "lc_h": 70, "uc": 90},
)

masters = ()

FAMILY_NAME = "{family_name}"
STYLE_NAME = "Regular"
'''

_FONT_PY = '''\
"""Wire System + glyphs/ into a Project."""

from __future__ import annotations

from pathlib import Path

from typekernel.project import Project

from system import FAMILY_NAME, STYLE_NAME, masters, system

ROOT = Path(__file__).resolve().parent

__all__ = ["FAMILY_NAME", "STYLE_NAME", "ROOT", "get_project"]


def get_project() -> Project:
    return Project(system, ROOT / "glyphs", masters=masters)
'''

_GLYPH_README = '''\
# glyphs/

One ``.py`` file per glyph. Example::

    from typekernel.draw import Writer
    from typekernel.project import glyph
    from typekernel.system import System

    @glyph("syn.example", group="fixture")
    def syn_example(system: System):
        return (
            Writer()
            .start((0, 0))
            .line((100, 0))
            .line((100, 100))
            .line((0, 100))
            .close()
            .build()
        )
'''


def _starters_root() -> Path:
    # typekernel/cli/new.py → typekernel/starters/
    return Path(__file__).resolve().parents[1] / "starters"


def create_project(
    name: str,
    *,
    parent: str | Path = ".",
    starter: str | None = None,
) -> Path:
    """Create project directory ``parent/name``.

    Omit ``starter`` (or pass ``empty``) for the empty scaffold. Pass
    ``latin-sans`` to copy ``starters/latin_sans`` (system, elements, control
    glyphs).
    """
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise ValueError(f"invalid project name: {name!r}")

    starter_key = starter or "empty"
    if starter_key in ("", "empty"):
        starter_key = "empty"
    elif starter_key not in STARTERS:
        known = ", ".join(sorted(STARTERS) + ["empty"])
        raise ValueError(f"unknown starter {starter!r}; choose from {known}")

    root = Path(parent).resolve() / name
    if root.exists():
        raise FileExistsError(f"project path already exists: {root}")

    if starter_key == "empty":
        glyphs = root / "glyphs"
        glyphs.mkdir(parents=True)
        family = name.replace("_", " ").title()
        (root / "system.py").write_text(
            _SYSTEM_PY.replace("{family_name}", family),
            encoding="utf-8",
        )
        (root / "font.py").write_text(_FONT_PY, encoding="utf-8")
        (glyphs / "README.md").write_text(_GLYPH_README, encoding="utf-8")
        return root

    src = _starters_root() / STARTERS[starter_key]
    if not src.is_dir():
        raise FileNotFoundError(f"starter template missing: {src}")
    shutil.copytree(
        src,
        root,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )
    # Stamp the project family name from the directory name.
    system_py = root / "system.py"
    if system_py.is_file():
        text = system_py.read_text(encoding="utf-8")
        family = name.replace("_", " ").title()
        text = text.replace('FAMILY_NAME = "Latin Sans"', f'FAMILY_NAME = "{family}"')
        system_py.write_text(text, encoding="utf-8")
    return root
