"""Brief → System intent layer (honest, typed, no aesthetics AI).

Maps a small closed vocabulary onto documented ``System`` / token defaults.
Does **not** score style consistency, originality, or beauty — those stay
visual (``tk proof``). Agents still own glyph geometry.

Cold-start agents: declare ``BRIEF`` (or ``INTENT``) in ``system.py``, write
matching prose in ``brief.md``, then let ``tk audit`` flag contradictions.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from typekernel.system.table import Overshoot, System, Zones

__all__ = [
    "Brief",
    "ContrastFeel",
    "Intent",
    "IntentMismatch",
    "OpennessFeel",
    "SlantFeel",
    "WeightFeel",
    "apply_intent",
    "check_intent",
    "pen_defaults_for",
    "system_from_intent",
]

ContrastFeel = Literal["low", "medium", "high"]
SlantFeel = Literal["upright", "italic", "steep"]
OpennessFeel = Literal["tight", "normal", "open"]
WeightFeel = Literal["light", "regular", "bold"]

# --- Published mapping tables (feel → numeric). Agents may fine-tune inside bands. ---

# ``tokens["pen_contrast"]``: lower = more elliptical (calligraphic). Matches Pen.
CONTRAST_TO_PEN: Mapping[ContrastFeel, float] = {
    "low": 0.82,  # near-circular
    "medium": 0.52,  # humanist starter
    "high": 0.28,  # chancery-like
}

# Acceptance bands for ``check_intent`` (inclusive).
CONTRAST_BAND: Mapping[ContrastFeel, tuple[float, float]] = {
    "low": (0.65, 1.0),
    "medium": (0.40, 0.65),
    "high": (0.12, 0.40),
}

# ``System.slant`` (Δx / Δy).
SLANT_TO_VALUE: Mapping[SlantFeel, float] = {
    "upright": 0.0,
    "italic": 0.18,
    "steep": 0.28,
}

SLANT_BAND: Mapping[SlantFeel, tuple[float, float]] = {
    "upright": (0.0, 0.05),
    "italic": (0.10, 0.24),
    "steep": (0.24, 0.45),
}

# Default pen angle when Intent.pen_angle_deg is omitted.
SLANT_TO_PEN_ANGLE: Mapping[SlantFeel, float] = {
    "upright": 0.0,
    "italic": 28.0,
    "steep": 38.0,
}

PEN_ANGLE_BAND_HALFWIDTH = 12.0  # ±deg around declared / derived target

# Width tokens as multiples of stem["lc"] (suggestive only — not geometry factories).
OPENNESS_TO_WIDTH_MUL: Mapping[OpennessFeel, tuple[float, float]] = {
    # (n_width / lc, o_width / lc)
    "tight": (5.0, 5.2),
    "normal": (5.55, 5.85),
    "open": (6.4, 6.8),
}

OPENNESS_BAND: Mapping[OpennessFeel, tuple[float, float]] = {
    # allowed n_width / lc
    "tight": (4.4, 5.25),
    "normal": (5.25, 6.1),
    "open": (6.1, 7.5),
}

# Regular-ish lc stems; relatives follow humanist proportions.
WEIGHT_TO_LC: Mapping[WeightFeel, float] = {
    "light": 52.0,
    "regular": 72.0,
    "bold": 100.0,
}

WEIGHT_BAND: Mapping[WeightFeel, tuple[float, float]] = {
    "light": (40.0, 60.0),
    "regular": (60.0, 88.0),
    "bold": (88.0, 130.0),
}


@dataclass(frozen=True, slots=True)
class Intent:
    """Typed design intent — closed vocab, documented numeric mapping.

    Forbidden: treating this as an aesthetics score or a glyph factory.
    Allowed: seeding / checking ``System.slant``, ``stem``, and pen/width tokens.
    """

    contrast: ContrastFeel = "medium"
    slant: SlantFeel = "upright"
    openness: OpennessFeel = "normal"
    weight: WeightFeel = "regular"
    pen_angle_deg: float | None = None


@dataclass(frozen=True, slots=True)
class Brief:
    """Prose (human) + typed Intent (library-checkable)."""

    prose: str
    intent: Intent


@dataclass(frozen=True, slots=True)
class IntentMismatch:
    """One contradiction between declared Intent and a ``System``."""

    field: str
    level: str  # warn | error
    message: str


def pen_defaults_for(intent: Intent) -> tuple[float, float]:
    """Return ``(pen_contrast, pen_angle_deg)`` for *intent*."""
    contrast = float(CONTRAST_TO_PEN[intent.contrast])
    if intent.pen_angle_deg is not None:
        angle = float(intent.pen_angle_deg)
    else:
        angle = float(SLANT_TO_PEN_ANGLE[intent.slant])
    return contrast, angle


def _stem_for_weight(weight: WeightFeel) -> dict[str, float]:
    lc = float(WEIGHT_TO_LC[weight])
    return {
        "lc": lc,
        "lc_h": round(lc * 0.80, 1),
        "uc": round(lc * 1.11, 1),
        "uc_h": round(lc * 0.89, 1),
    }


def _width_tokens(intent: Intent, stem_lc: float) -> dict[str, float]:
    n_mul, o_mul = OPENNESS_TO_WIDTH_MUL[intent.openness]
    return {
        "n_width": round(stem_lc * n_mul, 1),
        "o_width": round(stem_lc * o_mul, 1),
    }


def system_from_intent(
    intent: Intent,
    *,
    upm: float = 1000.0,
    zones: Zones | None = None,
    overshoot: Overshoot | None = None,
    extra_tokens: Mapping[str, float] | None = None,
) -> System:
    """Build a starting ``System`` from *intent* (initial seed, not a final face)."""
    stem = _stem_for_weight(intent.weight)
    contrast, angle = pen_defaults_for(intent)
    tokens: dict[str, float] = {
        "pen_contrast": contrast,
        "pen_angle_deg": angle,
        **_width_tokens(intent, stem["lc"]),
        "space_stem_mul": 2.5,
        "space_lsb_mul": 0.5,
        "lsb_lc": round(stem["lc"] * 0.5, 1),
        "lsb_uc": round(stem["uc"] * 0.55, 1),
    }
    if extra_tokens:
        tokens.update({str(k): float(v) for k, v in extra_tokens.items()})
    return System(
        upm=float(upm),
        zones=zones
        or Zones(base=0, x=500, cap=700, asc=750, desc=-200),
        overshoot=overshoot or Overshoot(round=12, pointed=10),
        stem=stem,
        slant=float(SLANT_TO_VALUE[intent.slant]),
        tokens=tokens,
    )


def apply_intent(base: System, intent: Intent) -> System:
    """Overlay mapped Intent fields onto *base*; keep unrelated tokens/stems."""
    contrast, angle = pen_defaults_for(intent)
    stem = dict(base.stem)
    weight_stem = _stem_for_weight(intent.weight)
    for key, value in weight_stem.items():
        stem[key] = value
    tokens = dict(base.tokens)
    tokens["pen_contrast"] = contrast
    tokens["pen_angle_deg"] = angle
    tokens.update(_width_tokens(intent, float(stem["lc"])))
    return base.tuned(
        stem=stem,
        slant=float(SLANT_TO_VALUE[intent.slant]),
        tokens=tokens,
    )


def check_intent(
    system: System,
    intent: Intent,
    *,
    require_pen_tokens: bool = True,
) -> list[IntentMismatch]:
    """Return mismatches when *system* contradicts declared *intent* bands.

    Structural absence of pen tokens is a warning when ``require_pen_tokens``
    (skeleton/pen projects). Never invents a pass/fail aesthetics score.
    """
    out: list[IntentMismatch] = []
    tokens = dict(system.tokens)

    # contrast → pen_contrast
    lo, hi = CONTRAST_BAND[intent.contrast]
    if "pen_contrast" not in tokens:
        if require_pen_tokens:
            out.append(
                IntentMismatch(
                    "contrast",
                    "warn",
                    f"intent.contrast={intent.contrast!r} but tokens['pen_contrast'] missing "
                    f"(expected ~{CONTRAST_TO_PEN[intent.contrast]} in [{lo}, {hi}])",
                )
            )
    else:
        pc = float(tokens["pen_contrast"])
        if not (lo <= pc <= hi):
            out.append(
                IntentMismatch(
                    "contrast",
                    "warn",
                    f"tokens['pen_contrast']={pc} outside intent.contrast={intent.contrast!r} "
                    f"band [{lo}, {hi}] (map default {CONTRAST_TO_PEN[intent.contrast]})",
                )
            )

    # slant
    s_lo, s_hi = SLANT_BAND[intent.slant]
    slant = abs(float(system.slant))
    if intent.slant == "upright":
        if slant > s_hi:
            out.append(
                IntentMismatch(
                    "slant",
                    "warn",
                    f"System.slant={system.slant} contradicts intent.slant='upright' "
                    f"(expected |slant|≤{s_hi})",
                )
            )
    elif not (s_lo <= slant <= s_hi):
        out.append(
            IntentMismatch(
                "slant",
                "warn",
                f"System.slant={system.slant} outside intent.slant={intent.slant!r} "
                f"band [{s_lo}, {s_hi}] (map default {SLANT_TO_VALUE[intent.slant]})",
            )
        )

    # pen angle
    target_angle = (
        float(intent.pen_angle_deg)
        if intent.pen_angle_deg is not None
        else float(SLANT_TO_PEN_ANGLE[intent.slant])
    )
    if "pen_angle_deg" not in tokens:
        if require_pen_tokens and intent.slant != "upright":
            out.append(
                IntentMismatch(
                    "pen_angle_deg",
                    "warn",
                    f"tokens['pen_angle_deg'] missing (intent target ~{target_angle})",
                )
            )
    else:
        angle = float(tokens["pen_angle_deg"])
        if abs(angle - target_angle) > PEN_ANGLE_BAND_HALFWIDTH:
            out.append(
                IntentMismatch(
                    "pen_angle_deg",
                    "warn",
                    f"tokens['pen_angle_deg']={angle} far from intent target {target_angle} "
                    f"(±{PEN_ANGLE_BAND_HALFWIDTH})",
                )
            )

    # weight → stem["lc"]
    w_lo, w_hi = WEIGHT_BAND[intent.weight]
    if "lc" not in system.stem:
        out.append(
            IntentMismatch(
                "weight",
                "warn",
                f"intent.weight={intent.weight!r} but stem['lc'] missing",
            )
        )
    else:
        lc = float(system.stem["lc"])
        if not (w_lo <= lc <= w_hi):
            out.append(
                IntentMismatch(
                    "weight",
                    "warn",
                    f"stem['lc']={lc} outside intent.weight={intent.weight!r} "
                    f"band [{w_lo}, {w_hi}] (map default {WEIGHT_TO_LC[intent.weight]})",
                )
            )

    # openness → n_width / lc
    o_lo, o_hi = OPENNESS_BAND[intent.openness]
    if "n_width" not in tokens or "lc" not in system.stem:
        out.append(
            IntentMismatch(
                "openness",
                "warn",
                f"intent.openness={intent.openness!r} needs stem['lc'] and tokens['n_width'] "
                f"(ratio band [{o_lo}, {o_hi}])",
            )
        )
    else:
        ratio = float(tokens["n_width"]) / float(system.stem["lc"])
        if not (o_lo <= ratio <= o_hi):
            out.append(
                IntentMismatch(
                    "openness",
                    "warn",
                    f"n_width/lc={ratio:.3f} outside intent.openness={intent.openness!r} "
                    f"band [{o_lo}, {o_hi}]",
                )
            )

    return out


def coerce_intent(value: Any) -> Intent | None:
    """Accept ``Intent``, ``Brief``, or a mapping with Intent fields."""
    if value is None:
        return None
    if isinstance(value, Brief):
        return value.intent
    if isinstance(value, Intent):
        return value
    if isinstance(value, Mapping):
        keys = ("contrast", "slant", "openness", "weight", "pen_angle_deg")
        kwargs = {k: value[k] for k in keys if k in value}
        return Intent(**kwargs)
    return None
