#!/usr/bin/env python3
"""Emit vision-review proof pack (no visual PASS asserts).

Writes ``artifacts/skill-validate/visual_accept_*.png`` and, when possible,
copies the same files to ``/workspace/uploads/`` for the vision agent.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from typekernel.compile import build_font
from typekernel.font import Font
from typekernel.optics.space import space_font
from typekernel.parts import DesignContext, FormSources
from typekernel.parts.style import Style
from typekernel.qa.proof import proof_labeled_waterfall

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "skill-validate"
UPLOADS = Path("/workspace/uploads")


def _compile(stem: float, style: Style, name: str, chars: str) -> Path:
    ctx = DesignContext.geometric_sans().tuned(
        stem=stem, x_height=548.0, sidebearing_ratio=0.09
    )
    from dataclasses import replace

    c = replace(ctx, style=style)
    fs = FormSources.from_context(ctx, style=style)
    drawn = {}
    for ch in chars:
        if ch == " ":
            continue
        try:
            drawn[ch] = fs.derive_one(ch)
        except Exception as exc:  # noqa: BLE001 — proof pack should skip missing
            print(f"skip {ch!r}: {exc}")
    spaced = space_font(drawn, c)
    font = Font.from_context(c, "VisualAccept", style_name=name)
    font.add_chars(spaced)
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    return Path(build_font(font, d, formats=("otf",)).binaries["otf"])


def _proof(otfs: list[tuple[str, Path]], text: str, dest: Path, *, sizes=(72, 120)) -> Path:
    return proof_labeled_waterfall(otfs, text, dest, sizes=sizes, width=1600)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    light, bold = 48.0, 120.0
    single = Style()  # product defaults: single a/g

    stems_chars = "nhmru"
    diag_chars = "vwxyk"
    ag_chars = "aagg aa gg agogo"
    caps_chars = "AHONV"
    figs_chars = "0123456789"
    ladder_chars = "nhmar"

    otf_l = _compile(light, single, "visual_accept_light", stems_chars + diag_chars + "ag" + caps_chars + figs_chars + "o")
    otf_b = _compile(bold, single, "visual_accept_bold", stems_chars + diag_chars + "ag" + caps_chars + figs_chars + "o")

    paths = [
        _proof([("light", otf_l), ("bold", otf_b)], "n h m r u", OUT / "visual_accept_stems.png"),
        _proof([("light", otf_l), ("bold", otf_b)], "v w x y k", OUT / "visual_accept_diags.png"),
        _proof([("light", otf_l), ("bold", otf_b)], "a aa g gg agogo", OUT / "visual_accept_ag.png"),
        _proof([("light", otf_l), ("bold", otf_b)], "A H O N V", OUT / "visual_accept_caps.png"),
        _proof([("light", otf_l), ("bold", otf_b)], "0123456789", OUT / "visual_accept_figs.png"),
        _proof(
            [("light", otf_l), ("bold", otf_b)],
            "nhmar soft",
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
