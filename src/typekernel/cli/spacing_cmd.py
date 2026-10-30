"""``tk spacing suggest|apply`` — opt-in sidebearing suggestions / Abs write."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from typekernel.plugins.spacing import (
    BBoxRhythmPlugin,
    OpticalAirPlugin,
    SpacingPlugin,
    TracyBandPlugin,
    run_apply,
    run_spacing_plugin,
    write_spacing_suggestions,
)
from typekernel.project import open_project

__all__ = ["spacing_apply", "spacing_suggest"]

_PLUGINS: dict[str, Callable[[], SpacingPlugin]] = {
    "bbox_rhythm": BBoxRhythmPlugin,
    "optical_air": OpticalAirPlugin,
    "tracy_bands": TracyBandPlugin,
}


def _parse_names(names: list[str] | str | None) -> list[str] | None:
    if names is None:
        return None
    if isinstance(names, str):
        parts = [p.strip() for p in names.split(",") if p.strip()]
        return parts or None
    return list(names)


def spacing_suggest(
    root: str | Path,
    *,
    out: str | Path | None = None,
    master: str | None = None,
    plugin: str = "bbox_rhythm",
    names: list[str] | str | None = None,
    include_pairs: bool = False,
) -> Path:
    """Write ``spacing-suggestions.json`` (or ``out``); never mutates the project."""
    root_path = Path(root).resolve()
    dest = Path(out) if out is not None else root_path / "spacing-suggestions.json"
    factory = _PLUGINS.get(plugin)
    if factory is None:
        raise ValueError(
            f"unknown spacing plugin {plugin!r}; choose from {sorted(_PLUGINS)}"
        )
    if plugin == "tracy_bands":
        plug: SpacingPlugin = TracyBandPlugin(include_pairs=include_pairs)
    else:
        plug = factory()
    glyph_names = _parse_names(names)
    with open_project(root_path) as session:
        suggestions = run_spacing_plugin(
            session, plug, master=master, names=glyph_names
        )
    return write_spacing_suggestions(suggestions, dest, plugin_id=plug.id)


def spacing_apply(
    root: str | Path,
    *,
    out: str | Path | None = None,
    master: str | None = None,
    plugin: str = "bbox_rhythm",
    names: list[str] | str | None = None,
    write: bool = False,
) -> Path:
    """Build Abs apply plan (dry-run default). ``write=True`` rewrites spacing.py.

    Contours are never edited. Plan JSON always written.
    """
    root_path = Path(root).resolve()
    dest = Path(out) if out is not None else root_path / "spacing-apply-plan.json"
    factory = _PLUGINS.get(plugin)
    if factory is None:
        raise ValueError(
            f"unknown spacing plugin {plugin!r}; choose from {sorted(_PLUGINS)}"
        )
    plug = factory()
    glyph_names = _parse_names(names)
    with open_project(root_path) as session:
        suggestions = run_spacing_plugin(
            session, plug, master=master, names=glyph_names
        )
        result = run_apply(session, suggestions, out=dest, write=write)
    return result.plan_path
