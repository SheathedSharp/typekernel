"""Per-glyph master outlines keyed by axis location.

A :class:`GlyphMasters` map holds designed outlines at discrete locations
(for example Regular at ``{"wght": 400}`` and Bold at ``{"wght": 700}``).
It does not interpolate and does not write designspace XML — that is
:mod:`typekernel.axes.designspace_export`.
"""

from __future__ import annotations

from typekernel.draw.drawing import Drawing
from typekernel.geo.outline import Outline


def _location_key(location: dict[str, float]) -> tuple[tuple[str, float], ...]:
    return tuple(sorted(location.items()))


class GlyphMasters:
    """Map axis locations to :class:`~typekernel.geo.outline.Outline` values.

    Locations are compared by exact float equality on each axis tag. Callers
    that need tolerance should normalise before ``add`` / ``get``.
    """

    def __init__(self) -> None:
        self._by_location: dict[tuple[tuple[str, float], ...], Outline] = {}

    def add(self, location: dict[str, float], outline: Outline) -> None:
        """Store ``outline`` at ``location``, replacing any previous entry."""
        self._by_location[_location_key(location)] = outline

    def add_drawing(self, location: dict[str, float], drawing: Drawing) -> None:
        """Store ``drawing.outline()`` at ``location``."""
        self.add(location, drawing.outline())

    def get(self, location: dict[str, float]) -> Outline:
        """Return the outline stored at exactly ``location``.

        Raises:
            KeyError: if no master was stored at that location.
        """
        key = _location_key(location)
        try:
            return self._by_location[key]
        except KeyError as exc:
            raise KeyError(f"no master at location {dict(key)}") from exc

    def __len__(self) -> int:
        return len(self._by_location)

    def locations(self) -> list[dict[str, float]]:
        """Return stored locations as plain dicts, sorted by axis tag."""
        return [dict(key) for key in sorted(self._by_location)]
