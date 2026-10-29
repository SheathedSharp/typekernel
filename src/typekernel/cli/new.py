"""``tk new`` — scaffold an empty typekernel project or copy a starter."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

__all__ = ["STARTERS", "create_project"]

STARTERS: dict[str, str] = {
    "latin-sans": "latin_sans",
    "latin-humanist-italic": "latin_humanist_italic",
    "latin-chancery": "latin_chancery",
    "latin-sans-italic": "latin_sans_italic",
}

_BRIEF_MD = """\
# Brief

Write the face in prose. Typed intent (contrast / slant / openness / weight) lives
on ``PROJECT.brief`` / ``system.py`` Intent helpers — see ``typekernel.system.intent``
and the font-design skill. ``tk audit`` warns when System drifts outside Intent bands;
it does not score beauty (use ``tk proof`` / ``tk see``).
"""

_SYSTEM_PY = '''\
"""Designer numeric table for this project."""

from __future__ import annotations

from typekernel.system import Brief, Intent, Overshoot, System, Zones

# Optional: typed intent checked by ``tk audit`` (see typekernel.system.intent).
# BRIEF = Brief(
#     prose="Describe the face; keep Intent fields honest.",
#     intent=Intent(contrast="medium", slant="upright", openness="normal", weight="regular"),
# )
# INTENT = BRIEF.intent

system = System(
    upm=1000,
    zones=Zones(base=0, x=500, cap=700, asc=750, desc=-200),
    overshoot=Overshoot(round=12, pointed=10),
    stem={"lc": 80, "lc_h": 70, "uc": 90},
)
'''

_PROJECT_PY = '''\
"""Project manifest — sole entry for typekernel loaders."""

from __future__ import annotations

from system import system

from typekernel.project import FamilyInfo, Project

__all__ = ["PROJECT"]

PROJECT = Project(
    info=FamilyInfo(family="{family_name}"),
    system=system,
    glyphs="glyphs",
)
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
    return Path(__file__).resolve().parents[1] / "starters"


def create_project(
    name: str,
    *,
    parent: str | Path = ".",
    starter: str | None = None,
) -> Path:
    """Create project directory ``parent/name``.

    Omit ``starter`` (or pass ``empty``) for the empty scaffold. Pass
    ``latin-sans``, ``latin-sans-italic``, ``latin-humanist-italic``, or ``latin-chancery`` to copy
    the matching starter (system, elements, glyph set, project.py).
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
        (root / "system.py").write_text(_SYSTEM_PY, encoding="utf-8")
        (root / "brief.md").write_text(_BRIEF_MD, encoding="utf-8")
        (root / "project.py").write_text(
            _PROJECT_PY.replace("{family_name}", family),
            encoding="utf-8",
        )
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
    family = name.replace("_", " ").title()
    project_py = root / "project.py"
    if project_py.is_file():
        text = project_py.read_text(encoding="utf-8")
        text, n = re.subn(
            r"FamilyInfo\(family=FAMILY_NAME\)",
            f'FamilyInfo(family="{family}")',
            text,
            count=1,
        )
        if not n:
            text, n = re.subn(
                r'FamilyInfo\(family="[^"]*"\)',
                f'FamilyInfo(family="{family}")',
                text,
                count=1,
            )
        if n:
            project_py.write_text(text, encoding="utf-8")
    system_py = root / "system.py"
    if system_py.is_file():
        stext = system_py.read_text(encoding="utf-8")
        stext, sn = re.subn(
            r'^FAMILY_NAME\s*=\s*"[^"]*"',
            f'FAMILY_NAME = "{family}"',
            stext,
            count=1,
            flags=re.MULTILINE,
        )
        if sn:
            system_py.write_text(stext, encoding="utf-8")
    return root
