#!/usr/bin/env python3
"""Emit vision-review proof pack (no visual PASS asserts).

Writes ``artifacts/skill-validate/visual_accept_*.png`` and, when possible,
copies the same files to ``/workspace/uploads/`` for the vision agent.

Every character that appears in a proof string is compiled into the OTF
(no ``.notdef`` boxes). Heavy masters use ``with_stem_relief``.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

from typekernel.compile import build_font
from typekernel.font import Font
from typekernel.optics.space import space_font
from typekernel.parts import DesignContext, FormSources
from typekernel.parts.style import Style
from typekernel.parts.weight_relief import STEM_RELIEF_ONSET
from typekernel.qa.proof import proof_labeled_waterfall

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "skill-validate"
UPLOADS = Path("/workspace/uploads")

# Proof strings — charset is the union of every char used here.
PROOFS: dict[str, str] = {
    "visual_accept_stems.png": "n h m r u",
    "visual_accept_diags.png": "v w x y k",
    "visual_accept_ag.png": "a aa g gg agogo",
    "visual_accept_ag_double.png": "a aa g gg agogo",
    "visual_accept_caps.png": "A H O N V",
    "visual_accept_figs.png": "0123456789",
    "visual_accept_ladder.png": "nhmar",
}


def _charset(*texts: str) -> str:
    seen: list[str] = []
    for text in texts:
        for ch in text:
            if ch == " " or ch in seen:
                continue
            seen.append(ch)
    return "".join(seen)


def _compile(stem: float, style: Style, name: str, chars: str) -> Path:
    ctx = DesignContext.geometric_sans().tuned(
        stem=stem, x_height=548.0, sidebearing_ratio=0.09
    )
    c = replace(ctx, style=style)
    fs = FormSources.from_context(ctx, style=style)
    if stem >= STEM_RELIEF_ONSET:
        fs = fs.with_stem_relief()
    drawn = {ch: fs.derive_one(ch) for ch in chars}
    spaced = space_font(drawn, c)
    font = Font.from_context(c, "VisualAccept", style_name=name)
    font.add_chars(spaced)
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    return Path(build_font(font, d, formats=("otf",)).binaries["otf"])


def _proof(
    otfs: list[tuple[str, Path]], text: str, dest: Path, *, sizes=(72, 120)
) -> Path:
    return proof_labeled_waterfall(otfs, text, dest, sizes=sizes, width=1600)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    light, bold, black = 48.0, 120.0, 168.0
    single = Style()
    double = Style(a_form="double", g_form="double")

    chars_single = _charset(*PROOFS.values())
    chars_double = _charset(PROOFS["visual_accept_ag_double.png"], "o")

    otf_l = _compile(light, single, "visual_accept_light", chars_single)
    otf_b = _compile(bold, single, "visual_accept_bold", chars_single)
    otf_k = _compile(black, single, "visual_accept_black", chars_single)
    otf_dl = _compile(light, double, "visual_accept_double_light", chars_double)
    otf_db = _compile(bold, double, "visual_accept_double_bold", chars_double)
    otf_dk = _compile(black, double, "visual_accept_double_black", chars_double)

    ladder = [("light", otf_l), ("bold", otf_b), ("black", otf_k)]
    paths = [
        _proof(ladder, PROOFS["visual_accept_stems.png"], OUT / "visual_accept_stems.png"),
        _proof(ladder, PROOFS["visual_accept_diags.png"], OUT / "visual_accept_diags.png"),
        _proof(ladder, PROOFS["visual_accept_ag.png"], OUT / "visual_accept_ag.png"),
        _proof(
            [("light", otf_dl), ("bold", otf_db), ("black", otf_dk)],
            PROOFS["visual_accept_ag_double.png"],
            OUT / "visual_accept_ag_double.png",
        ),
        _proof(ladder, PROOFS["visual_accept_caps.png"], OUT / "visual_accept_caps.png"),
        _proof(ladder, PROOFS["visual_accept_figs.png"], OUT / "visual_accept_figs.png"),
        _proof(
            ladder,
            PROOFS["visual_accept_ladder.png"],
            OUT / "visual_accept_ladder.png",
            sizes=(48, 72, 96, 128),
        ),
    ]

    print("wrote", len(paths), "proofs under", OUT)
    if UPLOADS.is_dir():
        for src in paths:
            shutil.copy2(src, UPLOADS / src.name)
            print("also", UPLOADS / src.name)
    else:
        print("note: /workspace/uploads not on this machine — copy proofs to the box for vision")
    print("SMOKE/proofs only — vision must review; no auto PASS.")


if __name__ == "__main__":
    main()
