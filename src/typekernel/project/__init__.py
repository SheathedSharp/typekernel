"""project — @glyph registry, directory discovery, master evaluation (§9.7a)."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import MappingProxyType, ModuleType

from typekernel.draw import CornerFiller, Drawing, EndFiller, apply_slots
from typekernel.font.glyph import Glyph
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
from typekernel.system import System

__all__ = [
    "GlyphSpec",
    "Master",
    "Project",
    "glyph",
    "unicodes_for_glyph_name",
]


class Project:
    """Load ``@glyph`` modules, evaluate masters, and emit ``font.Glyph``."""

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
        """Import every ``*.py`` under ``glyphs`` and collect ``@glyph`` specs."""
        root = self._glyphs.resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"glyphs path is not a directory: {root}")

        root_s = str(root)
        if root_s not in sys.path:
            sys.path.insert(0, root_s)
        # Project root (parent of glyphs/) holds elements.py / system.py.
        project_root = str(root.parent)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        for bare in ("elements", "system", "spacing"):
            mod = sys.modules.get(bare)
            if mod is None:
                continue
            mod_file = getattr(mod, "__file__", "") or ""
            if not mod_file.startswith(project_root):
                sys.modules.pop(bare, None)

        collected: dict[str, GlyphSpec] = {}
        with registration_target(collected):
            for path in sorted(root.rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                _load_glyph_module(root, path)

        self._specs = collected
        self._discovered = True

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
        drawing = build(system)
        if self._corners is not None or self._ends is not None:
            drawing = apply_slots(
                drawing,
                system,
                self._corners or {},
                self._ends or {},
            )
        return drawing

    def to_glyph(
        self,
        name: str,
        *,
        master: str | None = None,
        advance: float | None = None,
    ) -> Glyph:
        """``evaluate`` then wrap contours as ``font.Glyph``.

        Advance resolution when ``advance`` is omitted: ``default_advance``,
        else ``system.tokens['<name>_advance']``, else ``tokens['advance']``,
        else bbox width of the drawing. Unicodes are derived from the glyph
        name (AGL / single character) when available.
        """
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
    """Create missing parent package modules so dotted names are importable."""
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
    # Compile from current file bytes so same-second edits are not masked by
    # SourceFileLoader / __pycache__ mtime races (needed for ``tk diff``).
    source = path.read_text(encoding="utf-8")
    code = compile(source, str(path), "exec")
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__loader__ = None
    module.__package__ = name.rpartition(".")[0] or None
    sys.modules[name] = module
    exec(code, module.__dict__)
    return module
