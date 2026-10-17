"""Build agent trial reference trial: Regular + Bold OTFs for a fixed brief."""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path
from types import ModuleType

from typekernel.compile import build_font, compose_font_from_controls, reference_kern_classes
from typekernel.parts import Controls
from typekernel.qa.design_review import design_review
from typekernel.qa.proof import proof_labeled_waterfall
from typekernel.qa.sentence_gate import AGENT_SENTENCE, check_sentence_gate
from typekernel.qa.trial_protocol import FIXED_TRIAL_BRIEFS, snapshot_trial, write_trial_snapshot

_BRIEF_MODULES: dict[str, str] = {
    "brief-1": "design_warm_humanist",
    "brief-2": "design_editorial_geometric",
    "brief-3": "design_coding_clear",
}

_BRIEF_VARIANTS: dict[tuple[str, str], str] = {
    ("brief-2", "slab"): "design_editorial_slab",
    ("brief-2", "bracketed"): "design_editorial_bracketed",
}


def _load(brief_id: str, variant: str | None = None) -> ModuleType:
    if variant:
        key = (brief_id, variant)
        name = _BRIEF_VARIANTS.get(key)
        if name is None:
            known = sorted({f"{b}:{v}" for b, v in _BRIEF_VARIANTS})
            raise SystemExit(f"unknown variant {variant!r} for {brief_id!r}; use {known}")
        return importlib.import_module(name)
    name = _BRIEF_MODULES.get(brief_id)
    if name is None:
        raise SystemExit(f"unknown brief {brief_id!r}; use {sorted(_BRIEF_MODULES)}")
    return importlib.import_module(name)


def build(brief_id: str, out: Path, *, variant: str | None = None) -> int:
    mod = _load(brief_id, variant)
    regular: Controls = mod.controls()
    bold: Controls = mod.design_bold()
    family: str = mod.FAMILY_NAME
    baseline: Controls = mod.baseline_controls()

    brief = next(b for b in FIXED_TRIAL_BRIEFS if b.id == brief_id)
    snap = snapshot_trial(
        regular,
        brief=brief,
        round=1,
        apis_used=("Style", "terminal_style", "tuned_glyph", "design_module"),
    )
    write_trial_snapshot(out / "snapshot.json", snap)
    if not snap.l3_voice_ok or not snap.metrics_ok or snap.weight_ladder_r8_failures:
        return 1

    review = design_review(regular, baseline=baseline, out_dir=out / "review")
    print(review.summary())
    if review.charset_failures:
        return 2

    for label, sheet in (("Regular", regular), ("Bold", bold)):
        _report, failures = check_sentence_gate(sheet)
        if failures:
            print(f"{label} sentence gate:", *failures, sep="\n  ")
            return 3
        print(f"{label} sentence gate ok")

    kern_classes = reference_kern_classes(regular)
    otfs: list[tuple[str, Path]] = []
    for sheet, style, weight in (
        (regular, "Regular", 400),
        (bold, "Bold", 700),
    ):
        font = compose_font_from_controls(
            sheet,
            family,
            style,
            weight_class=weight,
            kern_classes=kern_classes,
        require_body_unlock=False,
        )
        built = build_font(font, out, formats=("otf",))
        otfs.append((style, built.binaries["otf"]))
        print(f"{style}: {built.binaries['otf']}")

    proof = proof_labeled_waterfall(otfs, AGENT_SENTENCE, out / "proof.png", sizes=(28, 48))
    print(f"proof: {proof}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", required=True, choices=sorted(_BRIEF_MODULES))
    parser.add_argument(
        "--variant",
        default=None,
        help="brief-2: slab | bracketed serif modules (default: geometric sans)",
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    return build(args.brief, args.out, variant=args.variant)


if __name__ == "__main__":
    raise SystemExit(main())
