"""Cut static instances from a variable font (P4-5 / ``varLib.instancer``)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from typekernel.axes.spec import Instance

__all__ = ["instance_static", "instance_statics"]


def instance_static(
    variable_font: str | Path,
    location: Mapping[str, float],
    out_path: str | Path,
) -> Path:
    """Instantiate ``variable_font`` at ``location`` and write a static TTF/OTF.

    ``location`` keys are axis tags (e.g. ``{"wght": 400}``). Uses
    ``fontTools.varLib.instancer``.
    """
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    src = Path(variable_font)
    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    font = TTFont(src)
    # instancer expects axis tag → value (or (min,max) range); pin to a point.
    pinned = {tag: float(val) for tag, val in location.items()}
    instanced = instancer.instantiateVariableFont(font, pinned, inplace=False)
    instanced.save(dest)
    return dest


def instance_statics(
    variable_font: str | Path,
    instances: Sequence[Instance],
    out_dir: str | Path,
    *,
    family_stem: str | None = None,
) -> list[Path]:
    """Write one static binary per :class:`Instance` under ``out_dir``."""
    vf = Path(variable_font)
    out = Path(out_dir)
    stem = family_stem or vf.stem.replace("-VF", "")
    written: list[Path] = []
    for inst in instances:
        style = "".join(ch for ch in inst.name if ch.isalnum() or ch in "-_")
        dest = out / f"{stem}-{style}{vf.suffix}"
        written.append(instance_static(vf, inst.location, dest))
    return written
