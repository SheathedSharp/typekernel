"""``tk see`` — live edit / context / overlay / diff views (no compile)."""

from __future__ import annotations

import time
from pathlib import Path

from typekernel.perceive.views import (
    SeeResult,
    context_view,
    diff_view,
    edit_view,
    overlay_view,
    reference_view,
    skeleton_view,
)
from typekernel.project import open_project

__all__ = ["see_project"]


def see_project(
    path: str | Path,
    glyph: str,
    *,
    out_dir: str | Path | None = None,
    master: str | None = None,
    masters: bool = False,
    context: bool = False,
    overlay: bool = False,
    diff: str | None = None,
    reference: str | Path | None = None,
    size: int = 512,
    watch: bool = False,
    skeleton: bool = False,
) -> list[Path]:
    """Render requested views for ``glyph``; return PNG paths.

    When ``watch`` is true, reload the project when sources change and
    re-render affected views (Ctrl-C to stop).
    """
    root = Path(path).resolve()
    out = Path(out_dir) if out_dir else root / "proofs" / "see"
    out.mkdir(parents=True, exist_ok=True)

    def _once() -> list[Path]:
        paths: list[Path] = []
        with open_project(root) as session:
            results: list[SeeResult] = []
            results.append(
                edit_view(
                    session,
                    glyph,
                    master=master,
                    size=size,
                    out=out / f"see-{glyph}.png",
                )
            )
            if skeleton:
                results.append(
                    skeleton_view(
                        session,
                        glyph,
                        master=master,
                        size=size,
                        out=out / f"see-{glyph}-skeleton.png",
                    )
                )
            if context:
                results.append(
                    context_view(
                        session,
                        glyph,
                        master=master,
                        size=size,
                        out=out / f"see-{glyph}-context.png",
                    )
                )
            if masters or overlay:
                results.append(
                    overlay_view(
                        session,
                        glyph,
                        size=size,
                        out=out / f"see-{glyph}-masters.png",
                    )
                )
            if diff is not None:
                against = None if diff == "" else diff
                results.append(
                    diff_view(
                        session,
                        glyph,
                        against=against,
                        master=master,
                        size=size,
                        out=out / f"see-{glyph}-diff.png",
                    )
                )
            if reference is not None:
                results.append(
                    reference_view(
                        session,
                        glyph,
                        reference=reference,
                        master=master,
                        size=size,
                        out=out / f"see-{glyph}-reference.png",
                    )
                )
            paths = [r.png for r in results]
        return paths

    if not watch:
        return _once()

    # --watch: poll ProjectSession.reload via fingerprint changes.
    last_paths = _once()
    try:
        while True:
            time.sleep(0.5)
            with open_project(root) as session:
                changed = session.reload()
            if changed:
                last_paths = _once()
                print(f"reloaded: {sorted(changed)}")
                for p in last_paths:
                    print(p)
    except KeyboardInterrupt:
        return last_paths
