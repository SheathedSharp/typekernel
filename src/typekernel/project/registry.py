"""@glyph registration and discovery collector (ARCHITECTURE.md / target §3.3)."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, TypeVar, cast

from typekernel.draw import Drawing
from typekernel.project.manifest import ComponentRef, Expect
from typekernel.system import System, validate_traits

__all__ = [
    "GlyphDraft",
    "GlyphFn",
    "GlyphSpec",
    "Master",
    "glyph",
    "registration_target",
]

PointLike = tuple[float, float] | Any  # Point or (x, y)


@dataclass(frozen=True, slots=True)
class GlyphDraft:
    """Builder return value: drawing plus optional anchors / components / note.

    ``skeleton`` (S4) holds a cubic/polyline midline for ``tk see --skeleton``.
    """

    drawing: Drawing
    anchors: Mapping[str, PointLike] = field(default_factory=dict)
    components: Sequence[ComponentRef] = ()
    note: str = ""
    skeleton: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchors", MappingProxyType(dict(self.anchors)))
        object.__setattr__(self, "components", tuple(self.components))


GlyphFn = Callable[[System], Drawing | GlyphDraft]
GlyphFnT = TypeVar("GlyphFnT", bound=GlyphFn)


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
    unicodes: tuple[int, ...] | None = None  # None = derive; () = unencoded
    traits: tuple[str, ...] = ()
    expect: Expect | None = None


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
        return
    target[spec.name] = spec


def glyph(
    name: str,
    *,
    unicodes: Sequence[int] | None = None,
    group: str = "",
    traits: Iterable[str] = (),
    expect: Expect | None = None,
) -> Callable[[GlyphFnT], GlyphFnT]:
    """Register a glyph builder. ``fn(system) -> Drawing | GlyphDraft``.

    ``unicodes=None`` derives from the glyph name (AGL / single character).
    ``unicodes=()`` marks the glyph unencoded (not in cmap).
    ``traits`` must be members of :data:`typekernel.system.TRAITS`.
    """
    if not name:
        raise ValueError("glyph name must be non-empty")
    trait_tuple = validate_traits(traits)
    uni_tuple: tuple[int, ...] | None
    if unicodes is None:
        uni_tuple = None
    else:
        uni_tuple = tuple(int(u) for u in unicodes)

    def decorator(fn: GlyphFnT) -> GlyphFnT:
        masters_mut: dict[str, GlyphFn] = {}
        spec = GlyphSpec(
            name=name,
            group=group,
            build=fn,
            masters=MappingProxyType(masters_mut),
            unicodes=uni_tuple,
            traits=trait_tuple,
            expect=expect,
        )
        _put(spec)

        def master(master_name: str) -> Callable[[GlyphFnT], GlyphFnT]:
            if not master_name:
                raise ValueError("master name must be non-empty")

            def master_decorator(mfn: GlyphFnT) -> GlyphFnT:
                masters_mut[master_name] = mfn
                _put(
                    GlyphSpec(
                        name=name,
                        group=group,
                        build=fn,
                        masters=MappingProxyType(masters_mut),
                        unicodes=uni_tuple,
                        traits=trait_tuple,
                        expect=expect,
                    )
                )
                return mfn

            return master_decorator

        marked: Any = fn
        marked.master = master
        marked.__glyph_name__ = name
        marked.__glyph_group__ = group
        marked.__glyph_unicodes__ = uni_tuple
        marked.__glyph_traits__ = trait_tuple
        return cast(GlyphFnT, marked)

    return decorator
