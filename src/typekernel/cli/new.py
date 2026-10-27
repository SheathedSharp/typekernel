"""``tk new`` — scaffold an empty typekernel project."""

from __future__ import annotations

from pathlib import Path

__all__ = ["create_project"]

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


def create_project(
    name: str,
    *,
    parent: str | Path = ".",
    starter: str | None = None,
) -> Path:
    """Create an empty project directory ``parent/name``.

    ``starter`` is accepted for forward compatibility; M2 only scaffolds the
    empty layout (``latin-sans`` content lands in M4).
    """
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise ValueError(f"invalid project name: {name!r}")
    # M2: empty template only; named starters arrive in M4.
    if (
        starter is not None
        and starter not in ("", "empty", "latin-sans")
    ):
        raise ValueError(
            f"unknown starter {starter!r}; M2 supports only the empty "
            "template (omit --starter, or pass latin-sans as a reserved name)"
        )

    root = Path(parent).resolve() / name
    if root.exists():
        raise FileExistsError(f"project path already exists: {root}")

    glyphs = root / "glyphs"
    glyphs.mkdir(parents=True)
    (root / "system.py").write_text(
        _SYSTEM_PY.replace("{family_name}", name.replace("_", " ").title()),
        encoding="utf-8",
    )
    (root / "font.py").write_text(_FONT_PY, encoding="utf-8")
    (glyphs / "README.md").write_text(_GLYPH_README, encoding="utf-8")
    return root
