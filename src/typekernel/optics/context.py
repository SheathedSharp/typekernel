"""OpticalContext — design parameters for optical adjustments.

These values are alignment-zone and overshoot *design* parameters. They are
not stroke widths, pen radii, or buffer distances.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpticalContext:
    """Design-space parameters that optical operators read.

    Attributes:
        units_per_em: Em square size (typically 1000).
        x_height: Height of lowercase flat tops (e.g. ``x``, ``z``).
        cap_height: Height of uppercase flat tops (e.g. ``H``, ``E``).
        overshoot_round: Extra distance round extrema push past alignment zones.
        overshoot_sharp: Extra distance sharp extrema may push (often smaller).
    """

    units_per_em: float = 1000.0
    x_height: float = 500.0
    cap_height: float = 700.0
    overshoot_round: float = 12.0
    overshoot_sharp: float = 0.0

    @classmethod
    def latin_defaults(cls) -> OpticalContext:
        """Return typical Latin defaults for a 1000 UPM design space.

        Chosen numbers (document, not universal truth):

        - ``units_per_em`` = 1000
        - ``x_height`` = 500
        - ``cap_height`` = 700 (matches the synthetic ``O`` fixture top)
        - ``overshoot_round`` = 12 (common ballpark for round tops/bottoms)
        - ``overshoot_sharp`` = 0 (sharp corners usually sit on the zone)

        These are Latin-leaning starting points. CJK or other scripts need their
        own factories later; do not treat this as a universal default.
        """
        return cls(
            units_per_em=1000.0,
            x_height=500.0,
            cap_height=700.0,
            overshoot_round=12.0,
            overshoot_sharp=0.0,
        )
