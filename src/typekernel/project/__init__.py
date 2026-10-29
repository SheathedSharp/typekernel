"""project — @glyph registry, Project, ProjectSession (ARCHITECTURE.md / target §3)."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType, ModuleType

from typekernel.draw import CornerFiller, Drawing, EndFiller, SlotFillError, apply_slots
from typekernel.font.glyph import Glyph
from typekernel.project.errors import GlyphBuildError, MigrationError
from typekernel.project.evaluate import (
    advance_from_drawing,
    drawing_to_glyph,
    unicodes_for_glyph_name,
)
from typekernel.project.registry import (
    GlyphSpec,
    Master,
    glyph,
    registration_target,
)
from typekernel.project.session import ProjectSession, open_project
from typekernel.system import System

__all__ = [
    "GlyphBuildError",
    "GlyphSpec",
    "Master",
    "MigrationError",
    "Project",
    "ProjectSession",
    "glyph",
    "open_project",
    "unicodes_for_glyph_name",
]


class Project:
    """Load ``@glyph`` modules, evaluate masters, and emit ``font.Glyph``.

    Prefer :func:`open_project` / :class:`ProjectSession` for on-disk projects
    (isolated imports). Constructing ``Project`` directly remains valid for
    in-memory / unit-test use.
    """

    def __init__(
        self,
        system: System,
        glyphs: str | Path,
        *,
        masters: Sequence[Master] = (),
        corners: Mapping[str, CornerFiller] | None = None,
        ends: Mapping[str, EndFiller] | None = None,
        default_advance: float | None = None,
    ) -> None:
        self._system = system
        self._glyphs = Path(glyphs)
        self._masters = tuple(masters)
        self._masters_by_name = {m.name: m for m in self._masters}
        self._corners = None if corners is None else dict(corners)
        self._ends = None if ends is None else dict(ends)
        self._default_advance = default_advance
        self._specs: dict[str, GlyphSpec] = {}
        self._discovered = False

    @property
    def system(self) -> System:
        return self._system

    @property
    def masters(self) -> tuple[Master, ...]:
        return self._masters

    def discover(self) -> None:
        """Import every ``*.py`` under ``glyphs`` and collect ``@glyph`` specs.

        For on-disk multi-project work prefer :func:`open_project`, which
        isolates ``system`` / ``elements`` / ``spacing`` via a meta-path finder.
        This method still supports unit tests that build a temporary glyphs
        tree without a full project root. When a sibling ``elements.py`` /
        ``system.py`` exists, they are bound as bare names for the duration of
        discovery so a stale ``sys.modules`` entry from another project cannot
        win.
        """
        if self._discovered:
            return
        root = self._glyphs.resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"glyphs path is not a directory: {root}")

        project_root = root.parent
        saved: dict[str, ModuleType | None] = {}
        owned: list[str] = []
        try:
            for bare in ("system", "elements", "spacing", "font"):
                path = project_root / f"{bare}.py"
                if not path.is_file():
                    continue
                saved[bare] = sys.modules.get(bare)
                qual = f"_typekernel_discover_{abs(hash(str(project_root))) & 0xFFFFFFFF:x}.{bare}"
                _ensure_parent_packages(qual)
                source = path.read_text(encoding="utf-8")
                code = compile(source, str(path), "exec")
                module = ModuleType(qual)
                module.__file__ = str(path)
                module.__loader__ = None
                module.__package__ = qual.rpartition(".")[0] or None
                sys.modules[qual] = module
                owned.append(qual)
                exec(code, module.__dict__)  # noqa: S102 - project modules by design
                sys.modules[bare] = module

            collected: dict[str, GlyphSpec] = {}
            with registration_target(collected):
                for path in sorted(root.rglob("*.py")):
                    if "__pycache__" in path.parts:
                        continue
                    _load_glyph_module(root, path)

            self._specs = collected
            self._discovered = True
        finally:
            for bare, prev in saved.items():
                if prev is None:
                    sys.modules.pop(bare, None)
                else:
                    sys.modules[bare] = prev
            for qual in owned:
                sys.modules.pop(qual, None)

    def specs(self) -> Mapping[str, GlyphSpec]:
        if not self._discovered:
            raise RuntimeError("call discover() before specs()")
        return MappingProxyType(self._specs)

    def evaluate(self, name: str, *, master: str | None = None) -> Drawing:
        """Run the glyph (or its master override) with the resolved System.

        Applies ``corners`` / ``ends`` via ``apply_slots`` when configured.
        """
        if not self._discovered:
            raise RuntimeError("call discover() before evaluate()")
        if name not in self._specs:
            raise KeyError(name)
        spec = self._specs[name]
        system = self._system
        build = spec.build
        if master is not None:
            if master in self._masters_by_name:
                system = self._masters_by_name[master].system
            if master in spec.masters:
                build = spec.masters[master]
        try:
            drawing = build(system)
            if self._corners is not None or self._ends is not None:
                try:
                    drawing = apply_slots(
                        drawing,
                        system,
                        self._corners or {},
                        self._ends or {},
                    )
                except SlotFillError as exc:
                    tag = exc.slot_tag or "?"
                    raise GlyphBuildError(name, master, exc, tag=tag) from exc
        except GlyphBuildError:
            raise
        except Exception as exc:
            raise GlyphBuildError(name, master, exc) from exc
        return drawing

    def to_glyph(
        self,
        name: str,
        *,
        master: str | None = None,
        advance: float | None = None,
    ) -> Glyph:
        """``evaluate`` then wrap contours as ``font.Glyph``."""
        drawing = self.evaluate(name, master=master)
        if advance is None:
            advance = self._resolve_advance(drawing, name=name)
        return drawing_to_glyph(name, drawing, advance=advance)

    def _resolve_advance(self, drawing: Drawing, *, name: str = "") -> float:
        if self._default_advance is not None:
            return float(self._default_advance)
        if name:
            keyed = self._system.tokens.get(f"{name}_advance")
            if keyed is not None:
                return float(keyed)
        token = self._system.tokens.get("advance")
        if token is not None:
            return float(token)
        return advance_from_drawing(drawing)


def _module_name(root: Path, path: Path) -> str:
    """Stable import name under a private namespace keyed by glyphs root."""
    key = abs(hash(str(root))) & 0xFFFFFFFF
    rel = path.relative_to(root)
    if path.name == "__init__.py":
        parts = rel.parent.parts
        suffix = ".".join(parts) if parts else "_root"
    else:
        suffix = ".".join(rel.with_suffix("").parts)
    return f"_typekernel_glyphs_{key:x}.{suffix}"


def _ensure_parent_packages(mod_name: str) -> None:
    parts = mod_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            pkg = ModuleType(parent)
            pkg.__path__ = []
            sys.modules[parent] = pkg


def _load_glyph_module(root: Path, path: Path) -> ModuleType:
    name = _module_name(root, path)
    _ensure_parent_packages(name)
    source = path.read_text(encoding="utf-8")
    code = compile(source, str(path), "exec")
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__loader__ = None
    module.__package__ = name.rpartition(".")[0] or None
    sys.modules[name] = module
    exec(code, module.__dict__)  # noqa: S102 - project glyph modules by design
    return module
