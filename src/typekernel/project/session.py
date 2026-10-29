"""ProjectSession — isolated project loading (target-architecture §3.5)."""

from __future__ import annotations

import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Any, cast

from typekernel.draw import Drawing, SlotFillError, apply_slots
from typekernel.font.font import Font
from typekernel.font.glyph import Glyph
from typekernel.project.errors import GlyphBuildError, MigrationError
from typekernel.project.evaluate import (
    advance_from_drawing,
    anchors_from_draft,
    components_from_draft,
    drawing_to_glyph,
    unicodes_for_glyph_name,
)
from typekernel.project.manifest import ComponentRef
from typekernel.project.registry import GlyphDraft, GlyphSpec, registration_target
from typekernel.system import System

__all__ = [
    "GlyphBuildError",
    "ProjectSession",
    "open_project",
]

# Top-level project modules that get namespaced as ``_tkproj_<hash>.<name>``.
_TOP_LEVEL_CANDIDATES = (
    "system",
    "elements",
    "spacing",
    "font",
    "project",
    "expect",
    "composites",
    "proofs",
)


@dataclass(frozen=True, slots=True)
class _Fingerprint:
    mtime_ns: int
    size: int
    sha1: str


def _sha1_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _fingerprint(path: Path) -> _Fingerprint:
    data = path.read_bytes()
    st = path.stat()
    return _Fingerprint(st.st_mtime_ns, st.st_size, _sha1_bytes(data))


def _ns_for(root: Path) -> str:
    digest = hashlib.sha1(str(root.resolve()).encode("utf-8")).hexdigest()[:12]
    return f"_tkproj_{digest}"


def _ensure_parent_packages(mod_name: str) -> None:
    parts = mod_name.split(".")
    for i in range(1, len(parts)):
        parent = ".".join(parts[:i])
        if parent not in sys.modules:
            pkg = ModuleType(parent)
            pkg.__path__ = []
            sys.modules[parent] = pkg


class _ProjectFinder(importlib.abc.MetaPathFinder):
    """Resolve bare project-root module names to ``_tkproj_<hash>.*`` modules.

    Only active while its owning :class:`ProjectSession` is the current session.
    Glyph files keep writing ``from elements import …``; the finder maps the
    bare name onto the namespaced module without putting the project root on
    ``sys.path``.
    """

    def __init__(self, session: ProjectSession) -> None:
        self._session = session

    def find_spec(
        self,
        fullname: str,
        path: Any = None,
        target: ModuleType | None = None,
    ) -> importlib.machinery.ModuleSpec | None:
        session = self._session
        if not session._active:
            return None
        ns = session._ns
        # Already-namespaced: ``_tkproj_xxx.elements`` or ``_tkproj_xxx.glyphs…``
        if fullname == ns or fullname.startswith(ns + "."):
            bare = fullname[len(ns) + 1 :] if fullname.startswith(ns + ".") else ""
            if not bare:
                return None
            return session._spec_for_bare(bare, qualname=fullname)
        # Bare top-level project module (elements / system / …).
        if "." in fullname:
            return None
        if fullname not in session._top_level_files:
            return None
        # Prefer existing alias so reload keeps identity until we replace it.
        return session._spec_for_bare(fullname, qualname=f"{ns}.{fullname}")


@dataclass
class ProjectSession:
    """Isolated view of one project root (target-architecture §3.5)."""

    root: Path
    # Filled during ``open``; typed loosely until P1-2 freezes Project.
    project: Any = None
    _ns: str = ""
    _active: bool = False
    _finder: _ProjectFinder | None = None
    _top_level_files: dict[str, Path] = field(default_factory=dict)
    _fingerprints: dict[str, _Fingerprint] = field(default_factory=dict)
    # bare name → namespaced module name
    _loaded: dict[str, str] = field(default_factory=dict)
    # glyph file rel posix → module name
    _glyph_modules: dict[str, str] = field(default_factory=dict)
    # module name → set of bare project deps it imported (best-effort)
    _deps: dict[str, set[str]] = field(default_factory=dict)
    _specs: dict[str, GlyphSpec] = field(default_factory=dict)
    # cache key (glyph, master, slots, dep fingerprint) → Drawing | GlyphDraft-like
    _eval_cache: dict[tuple[Any, ...], Any] = field(default_factory=dict)
    _dep_fingerprint: str = ""
    # aliased bare names we installed into sys.modules
    _aliases: list[str] = field(default_factory=list)
    # all sys.modules keys we own (ns package + modules + glyph modules)
    _owned_modules: set[str] = field(default_factory=set)

    def specs(self) -> Mapping[str, GlyphSpec]:
        return MappingProxyType(self._specs)

    def evaluate(
        self,
        name: str,
        *,
        master: str | None = None,
        slots: bool = True,
    ) -> GlyphDraft:
        """Run the glyph builder (and optional slot fill); return a GlyphDraft."""
        if name not in self._specs:
            raise KeyError(name)
        cache_key = (name, master, slots, self._dep_fingerprint)
        cached = self._eval_cache.get(cache_key)
        if cached is not None:
            return cast(GlyphDraft, cached)

        spec = self._specs[name]
        project = self.project
        system: System = project.system
        build = spec.build
        masters_by_name = {m.name: m for m in project.masters}
        if master is not None:
            if master in masters_by_name:
                system = masters_by_name[master].system
            if master in spec.masters:
                build = spec.masters[master]
        note = ""
        anchors: dict[str, object] = {}
        components: tuple[ComponentRef, ...] = ()
        try:
            result = build(system)
            if isinstance(result, Drawing):
                drawing = result
            else:
                drawing = result.drawing
                anchors = dict(result.anchors)
                components = tuple(result.components)
                note = result.note
            # Combining marks sit on anchors; corner/end fillers are for base letters.
            skip_slots = "mark" in spec.traits or "spacing-mark" in spec.traits
            if (
                slots
                and not skip_slots
                and (project.corners is not None or project.ends is not None)
            ):
                try:
                    drawing = apply_slots(
                        drawing,
                        system,
                        project.corners or {},
                        project.ends or {},
                    )
                except SlotFillError as exc:
                    raise GlyphBuildError(
                        name, master, exc, tag=exc.slot_tag or "?"
                    ) from exc
        except GlyphBuildError:
            raise
        except Exception as exc:
            raise GlyphBuildError(name, master, exc) from exc

        draft = GlyphDraft(
            drawing=drawing,
            anchors=anchors,
            components=components,
            note=note,
        )
        self._eval_cache[cache_key] = draft
        return draft

    def glyph(self, name: str, *, master: str | None = None) -> Glyph:
        """Evaluate then wrap as ``font.Glyph`` (anchors/components/unicodes)."""
        draft = self.evaluate(name, master=master, slots=True)
        spec = self._specs[name]
        if "mark" in spec.traits and "spacing-mark" not in spec.traits:
            advance = 0.0
        else:
            advance = self._resolve_advance(draft.drawing, name=name)
        if spec.unicodes is None:
            unicodes = unicodes_for_glyph_name(name)
        else:
            unicodes = spec.unicodes
        return drawing_to_glyph(
            name,
            draft.drawing,
            advance=advance,
            unicodes=unicodes,
            anchors=anchors_from_draft(draft.anchors),
            components=components_from_draft(tuple(draft.components)),
        )

    def _resolve_advance(self, drawing: Drawing, *, name: str = "") -> float:
        """Bbox / global ``advance`` token. Per-glyph ``*_advance`` removed in P1-4."""
        del name  # per-glyph token path deleted; metrics pack sets final advances
        system = self.project.system
        token = system.tokens.get("advance")
        if token is not None:
            return float(token)
        return advance_from_drawing(drawing)

    def font(self, *, master: str | None = None, family_name: str | None = None, style_name: str = "Regular") -> Font:
        """Assemble a Font from every registered glyph (spacing applied when present)."""
        from typekernel.cli.load import apply_project_spacing

        project = self.project
        system = project.system
        if master is not None:
            by_name = {m.name: m for m in project.masters}
            if master not in by_name:
                raise KeyError(f"unknown master {master!r}")
            system = by_name[master].system
        family = family_name or self.root.name
        font = Font.from_system(system, family, style_name)
        for name in self._specs:
            font.add_glyph(self.glyph(name, master=master), replace=True)
        if project.composites:
            from typekernel.project.compose import compose

            base_map = {g.name: g for g in font}
            for comp_name, spec in project.composites.items():
                font.add_glyph(
                    compose(spec, base_map, name=comp_name),
                    replace=True,
                )
        apply_project_spacing(font, project, self.root)
        # OpenType features from naming suffixes + features/*.fea
        from typekernel.features import assemble_features

        glyph_names = {g.name for g in font} | set(self._specs) | set(project.composites)
        font.features = assemble_features(
            glyph_names,
            fea_dir=project.features.fea_dir,
            root=self.root,
            extra=tuple(project.features.extra),
        )
        return font

    def reload(self) -> set[str]:
        """Re-import changed project modules; return affected glyph names."""
        if not self._active:
            raise RuntimeError("session is closed")
        changed_bares: set[str] = set()
        for bare, path in self._top_level_files.items():
            fp = _fingerprint(path)
            prev = self._fingerprints.get(bare)
            if prev is None or fp != prev:
                changed_bares.add(bare)
                self._fingerprints[bare] = fp

        # Glyph / mark file changes.
        changed_glyph_rels: set[str] = set()

        def _scan_changes(label: str, path_value: str | Path | None) -> None:
            if path_value is None:
                return
            _p = Path(path_value)
            tree = (_p if _p.is_absolute() else self.root / _p).resolve()
            if not tree.is_dir():
                return
            for path in sorted(tree.rglob("*.py")):
                if "__pycache__" in path.parts:
                    continue
                rel = path.relative_to(tree).as_posix()
                key = f"{label}:{rel}"
                fp = _fingerprint(path)
                prev = self._fingerprints.get(key)
                if prev is None or fp != prev:
                    changed_glyph_rels.add(f"{label}:{rel}")
                    self._fingerprints[key] = fp

        _scan_changes("glyphs", self.project.glyphs)
        _scan_changes("marks", self.project.marks)

        if not changed_bares and not changed_glyph_rels:
            return set()

        # Reload changed top-level modules (and any that depend on them).
        to_reload = set(changed_bares)
        # Cascade: if elements changed, anything that listed it as a dep reloads.
        for mod_name, deps in self._deps.items():
            if deps & changed_bares:
                # Map module name back to bare if it's a top-level.
                for bare, qname in self._loaded.items():
                    if qname == mod_name:
                        to_reload.add(bare)
        for bare in sorted(to_reload):
            self._load_top_level(bare, force=True)

        # Refresh aliases after reload.
        self._install_aliases()

        # Re-discover glyphs when any glyph file or a top-level dep changed.
        affected: set[str] = set()
        if changed_bares or changed_glyph_rels:
            before = set(self._specs)
            self._discover_glyphs()
            after = set(self._specs)
            # All current glyphs depend on elements/system at least.
            if changed_bares:
                affected |= after
            else:
                # Map changed glyph files → registered names by re-importing;
                # simplest honest answer: all specs whose module file changed.
                # We don't track per-glyph file precisely after registration;
                # return all specs when any glyph file changed.
                affected |= after
            affected |= before  # removed names also "affected"
            affected |= after

        self._eval_cache.clear()
        self._recompute_dep_fingerprint()
        return affected

    # --- internal ---------------------------------------------------------

    def _open(self) -> None:
        self.root = self.root.resolve()
        if not self.root.is_dir():
            raise FileNotFoundError(f"project root is not a directory: {self.root}")
        self._ns = _ns_for(self.root)
        self._finder = _ProjectFinder(self)
        self._active = True
        sys.meta_path.insert(0, self._finder)
        _ensure_parent_packages(self._ns)
        self._owned_modules.add(self._ns)

        # Index top-level .py files.
        for bare in _TOP_LEVEL_CANDIDATES:
            path = self.root / f"{bare}.py"
            if path.is_file():
                self._top_level_files[bare] = path

        # Drop stale bare aliases from a previous session so ``from system
        # import …`` inside project.py cannot resolve the wrong module.
        for bare in list(self._top_level_files):
            sys.modules.pop(bare, None)

        # Load every top-level module under the namespace; alias immediately
        # so later files (project.py) can ``from system import …``.
        for bare in list(self._top_level_files):
            self._load_top_level(bare, force=True)
            sys.modules[bare] = sys.modules[self._loaded[bare]]
            if bare not in self._aliases:
                self._aliases.append(bare)

        # Obtain Project (P1-1: font.get_project; P1-2 switches to PROJECT).
        self.project = self._load_project_object()
        self._discover_glyphs()
        self._recompute_dep_fingerprint()

    def _close(self) -> None:
        self._active = False
        if self._finder is not None and self._finder in sys.meta_path:
            sys.meta_path.remove(self._finder)
        self._finder = None
        # Drop bare aliases first so other code cannot see our modules.
        for bare in self._aliases:
            mod = sys.modules.get(bare)
            qname = self._loaded.get(bare)
            if qname is not None and mod is sys.modules.get(qname):
                sys.modules.pop(bare, None)
        self._aliases.clear()
        # Drop every module we own.
        for name in list(self._owned_modules):
            sys.modules.pop(name, None)
        self._owned_modules.clear()
        # Also drop any leftover ``_tkproj_<hash>.*`` that slipped in.
        prefix = self._ns + "."
        for name in list(sys.modules):
            if name == self._ns or name.startswith(prefix):
                sys.modules.pop(name, None)
        self._eval_cache.clear()
        self._specs.clear()
        importlib.invalidate_caches()

    def _load_project_object(self) -> Any:
        """Load ``PROJECT`` from ``project.py``; reject legacy conventions."""
        from typekernel.project.manifest import Project

        mapping = {
            "font.get_project / font.project": "project.py → PROJECT",
            "FAMILY_NAME / STYLE_NAME": "Project.info.family / Project.style_name",
            "MASTER_LOCATIONS": "MasterSpec.location on Project.masters",
            "AUDIT_STEMS": "Project.audit.stems (AuditConfig)",
            "EXTRA_CHECKS / CHECKS": "Project.audit.extra_checks",
            "BRIEF (as load entry)": "Project.brief",
            "spacing.apply_spacing (as sole advance path)": "Project.metrics + typekernel.metrics",
        }
        map_lines = "\n".join(f"  {old} → {new}" for old, new in mapping.items())

        if "project" in self._loaded:
            mod = sys.modules[self._loaded["project"]]
            if hasattr(mod, "PROJECT"):
                project = mod.PROJECT
                if not isinstance(project, Project):
                    raise TypeError(f"PROJECT must be Project, got {type(project)!r}")
                return project
            raise MigrationError(
                f"{self.root / 'project.py'} must export PROJECT = Project(...). "
                f"Old conventions are not loaded:\n{map_lines}",
                mapping=mapping,
            )

        hints: list[str] = []
        if "font" in self._loaded:
            font_mod = sys.modules[self._loaded["font"]]
            if hasattr(font_mod, "get_project") or hasattr(font_mod, "project"):
                hints.append("font.get_project / font.project")
        if "system" in self._loaded:
            sys_mod = sys.modules[self._loaded["system"]]
            for name in (
                "FAMILY_NAME",
                "STYLE_NAME",
                "MASTER_LOCATIONS",
                "AUDIT_STEMS",
                "EXTRA_CHECKS",
                "CHECKS",
            ):
                if hasattr(sys_mod, name):
                    hints.append(name)
        detail = ""
        if hints:
            detail = " Detected legacy names: " + ", ".join(hints) + "."
        raise MigrationError(
            f"no project.py with PROJECT in {self.root}.{detail}\n"
            f"Migrate to project.py → PROJECT. Old → new field map:\n{map_lines}",
            mapping=mapping,
        )

    def _spec_for_bare(self, bare: str, *, qualname: str) -> importlib.machinery.ModuleSpec | None:
        # Glyph submodule path: ``glyphs.lower.n`` under glyphs/
        if bare.startswith("glyphs.") or bare == "glyphs":
            return None  # glyph modules loaded explicitly
        path = self._top_level_files.get(bare.split(".", 1)[0] if "." in bare else bare)
        if path is None:
            # Could be a subpackage path — not used today.
            return None
        if "." in bare:
            return None
        spec = importlib.util.spec_from_file_location(qualname, path)
        return spec

    def _load_top_level(self, bare: str, *, force: bool = False) -> ModuleType:
        path = self._top_level_files[bare]
        qualname = f"{self._ns}.{bare}"
        if not force and qualname in sys.modules and bare in self._loaded:
            return sys.modules[qualname]
        self._fingerprints[bare] = _fingerprint(path)
        # Drop old module so exec rebinds cleanly.
        sys.modules.pop(qualname, None)
        _ensure_parent_packages(qualname)
        source = path.read_text(encoding="utf-8")
        code = compile(source, str(path), "exec")
        module = ModuleType(qualname)
        module.__file__ = str(path)
        module.__loader__ = None
        module.__package__ = self._ns
        sys.modules[qualname] = module
        self._owned_modules.add(qualname)
        self._loaded[bare] = qualname
        # Track deps by noting which project top-levels are already aliased
        # when this module finishes executing (best-effort).
        before = set(self._aliases)
        exec(code, module.__dict__)  # noqa: S102 - project code by design
        # Deps = top-level names this module can see; record intersection with
        # known project modules other than itself.
        deps = (set(self._top_level_files) - {bare}) & (
            before | set(self._loaded)
        )
        self._deps[qualname] = deps
        return module

    def _install_aliases(self) -> None:
        """Point bare names at our namespaced modules for project imports."""
        for bare, qualname in self._loaded.items():
            sys.modules[bare] = sys.modules[qualname]
            if bare not in self._aliases:
                self._aliases.append(bare)

    def _discover_glyphs(self) -> None:
        project = self.project
        collected: dict[str, GlyphSpec] = {}
        with registration_target(collected):
            self._scan_glyph_tree(
                collected, label="glyphs", path_value=project.glyphs, required=True
            )
            if project.marks is not None:
                self._scan_glyph_tree(
                    collected, label="marks", path_value=project.marks, required=False
                )
        self._specs = collected

    def _scan_glyph_tree(
        self,
        collected: dict[str, GlyphSpec],
        *,
        label: str,
        path_value: str | Path,
        required: bool,
    ) -> None:
        path = Path(path_value)
        root = path if path.is_absolute() else (self.root / path)
        root = root.resolve()
        if not root.is_dir():
            if required:
                raise FileNotFoundError(f"{label} path is not a directory: {root}")
            return
        # Drop prior fingerprints for this tree so removed files do not linger.
        prefix = f"{label}:"
        for key in [k for k in self._fingerprints if k.startswith(prefix)]:
            del self._fingerprints[key]
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(root)
            self._load_glyph_module(root, path, rel, ns_leaf=label)
            key = f"{label}:{rel.as_posix()}"
            self._fingerprints[key] = _fingerprint(path)

    def _load_glyph_module(
        self, root: Path, path: Path, rel: Path, *, ns_leaf: str = "glyphs"
    ) -> ModuleType:
        if path.name == "__init__.py":
            parts = rel.parent.parts
            suffix = ".".join(parts) if parts else "_root"
        else:
            suffix = ".".join(rel.with_suffix("").parts)
        qualname = f"{self._ns}.{ns_leaf}.{suffix}"
        _ensure_parent_packages(qualname)
        source = path.read_text(encoding="utf-8")
        code = compile(source, str(path), "exec")
        module = ModuleType(qualname)
        module.__file__ = str(path)
        module.__loader__ = None
        module.__package__ = qualname.rpartition(".")[0] or None
        sys.modules[qualname] = module
        self._owned_modules.add(qualname)
        self._glyph_modules[rel.as_posix()] = qualname
        exec(code, module.__dict__)  # noqa: S102 - project glyph modules by design
        return module

    def _recompute_dep_fingerprint(self) -> None:
        parts = [
            f"{k}:{fp.sha1}"
            for k, fp in sorted(self._fingerprints.items())
        ]
        self._dep_fingerprint = _sha1_bytes("|".join(parts).encode("utf-8"))


@contextmanager
def open_project(root: str | Path) -> Iterator[ProjectSession]:
    """Open an isolated :class:`ProjectSession` for ``root``."""
    session = ProjectSession(root=Path(root))
    try:
        session._open()
        yield session
    finally:
        if session._active:
            session._close()
