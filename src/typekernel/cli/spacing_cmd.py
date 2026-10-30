"""``tk spacing suggest`` — opt-in sidebearing suggestions (plugins.spacing)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from typekernel.plugins.spacing import (
    BBoxRhythmPlugin,
    OpticalAirPlugin,
    SpacingPlugin,
    run_spacing_plugin,
    write_spacing_suggestions,
)
from typekernel.project import open_project

__all__ = ["spacing_suggest"]

_PLUGINS: dict[str, Callable[[], SpacingPlugin]] = {
    "bbox_rhythm": BBoxRhythmPlugin,
    "optical_air": OpticalAirPlugin,
}


def spacing_suggest(
    root: str | Path,
    *,
    out: str | Path | None = None,
    master: str | None = None,
    plugin: str = "bbox_rhythm",
    names: list[str] | None = None,
) -> Path:
    """Write ``spacing-suggestions.json`` (or ``out``); never mutates the project."""
    root_path = Path(root).resolve()
    dest = Path(out) if out is not None else root_path / "spacing-suggestions.json"
    factory = _PLUGINS.get(plugin)
    if factory is None:
        raise ValueError(
            f"unknown spacing plugin {plugin!r}; choose from {sorted(_PLUGINS)}"
        )
    plug = factory()
    with open_project(root_path) as session:
        suggestions = run_spacing_plugin(
            session, plug, master=master, names=names
        )
    return write_spacing_suggestions(suggestions, dest, plugin_id=plug.id)
