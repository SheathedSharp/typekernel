"""Write a minimal weight-axis ``.designspace`` via fontTools.

Uses ``fontTools.designspaceLib`` only — no hand-rolled XML. STAT table
crafting and full VF packaging are out of scope here.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, SourceDescriptor

# (source name, weight location, UFO filename placeholder)
WeightSource = tuple[str, float, str]


def write_weight_designspace(
    path: str | Path,
    axis_min: float,
    axis_max: float,
    sources: Sequence[WeightSource],
    *,
    axis_default: float | None = None,
    axis_name: str = "weight",
) -> Path:
    """Write a ``.designspace`` with a single ``wght`` axis and the given sources.

    Each entry in ``sources`` is ``(name, weight_location, ufo_filename)``.
    Filenames are path strings only (placeholders are fine); this function does
    not create UFO or font binaries.

    Returns:
        The path written.
    """
    if axis_min > axis_max:
        raise ValueError(f"axis_min ({axis_min}) must be <= axis_max ({axis_max})")
    if not sources:
        raise ValueError("at least one source is required")

    default = axis_default if axis_default is not None else axis_min

    document = DesignSpaceDocument()

    axis = AxisDescriptor()
    axis.name = axis_name
    axis.tag = "wght"
    axis.minimum = float(axis_min)
    axis.maximum = float(axis_max)
    axis.default = float(default)
    document.addAxis(axis)

    for name, weight, filename in sources:
        source = SourceDescriptor()
        source.name = name
        source.filename = filename
        source.location = {axis_name: float(weight)}
        document.addSource(source)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    document.write(out)
    return out
