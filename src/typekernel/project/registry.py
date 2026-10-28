"""@glyph registration and discovery collector (ARCHITECTURE.md Project / @glyph / Master)."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, TypeVar, cast

from typekernel.draw import Drawing
from typekernel.system import System

__all__ = ["GlyphFn", "GlyphSpec", "Master", "glyph", "registration_target"]

GlyphFn = Callable[[System], Drawing]
F = TypeVar("F", bound=GlyphFn)


@dataclass(frozen=True, slots=True)
class Master:
    """A named System variant for master-specific evaluation."""

    name: str
    system: System


@dataclass(frozen=True, slots=True)
class GlyphSpec:
    """Registered glyph builder plus optional per-master overrides."""

    name: str
    group: str
    build: GlyphFn
    masters: Mapping[str, GlyphFn]


# Stack of collect dicts; discover() pushes one so @glyph lands there.
_targets: list[dict[str, GlyphSpec]] = []


@contextmanager
def registration_target(into: dict[str, GlyphSpec]) -> Iterator[None]:
    """Route ``@glyph`` registrations into ``into`` for the duration."""
    _targets.append(into)
    try:
        yield
    finally:
        _targets.pop()


def _current_target() -> dict[str, GlyphSpec] | None:
    return _targets[-1] if _targets else None


def _put(spec: GlyphSpec) -> None:
    target = _current_target()
    if target is None:
        # Import outside discover(): keep silent so accidental imports don't
        # crash; discover() only reads its own target.
        return
    # Last registration wins (reload-safe; master() refreshes the same entry).
    target[spec.name] = spec


def glyph(name: str, *, group: str = "") -> Callable[[F], F]:
    """Register a glyph builder. ``fn(system) -> Drawing``.

    Attach master overrides with ``@fn.master("Black")`` on a second function
    of the same shape. Glyph ``name`` is a production name (may be a letter in
    *projects*); kernel tests must still use synthetic names (架构守卫 rule 5).
    """
    if not name:
        raise ValueError("glyph name must be non-empty")

    def decorator(fn: F) -> F:
        masters_mut: dict[str, GlyphFn] = {}
        spec = GlyphSpec(
            name=name,
            group=group,
            build=fn,
            masters=MappingProxyType(masters_mut),
        )
        _put(spec)

        def master(master_name: str) -> Callable[[F], F]:
            if not master_name:
                raise ValueError("master name must be non-empty")

            def master_decorator(mfn: F) -> F:
                masters_mut[master_name] = mfn
                # Refresh the registry entry (proxy still views masters_mut).
                _put(
                    GlyphSpec(
                        name=name,
                        group=group,
                        build=fn,
                        masters=MappingProxyType(masters_mut),
                    )
                )
                return mfn

            return master_decorator

        marked: Any = fn
        marked.master = master
        marked.__glyph_name__ = name
        marked.__glyph_group__ = group
        return cast(F, marked)

    return decorator
