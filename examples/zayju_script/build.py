"""Build ZayJu Letter Script Regular — sequential style gate, then specimen proofs + OTF.

Run from repo root::

    PYTHONPATH=src python examples/zayju_script/build.py

Honest topology: calligraphy skeletons in ``design.py`` expanded with a
contrast broad-nib pen via ``trace_letter``. Writing slant is baked into
centerline coordinates — not ``oblique_font`` / lean / tracking.

``check_sentence_gate`` does **not** apply (not a Controls-derived face).
Primary acceptance artifacts are the filled brief PNGs.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from design import (
    BRIEF_SENTENCE,
    CHARSET,
    CONTROL_GLYPH,
    DESIGN_ORDER,
    build_charset_sequential,
    script_context,
)
from PIL import Image, ImageDraw

from typekernel.compile import build_font
from typekernel.font import Font
from typekernel.geo.contour import signed_area
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.optics.space import pair_gap_optical, space_font
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.metrics import KernTable, fit_glyph_pair_kerns, rhythm_from_control_glyphs
from typekernel.qa.proof import proof_charset_grid
from typekernel.qa.specimen_png import render_outline_png

OUT_DIR = Path(__file__).resolve().parent / "out"
FAMILY = "ZayJu Letter Script"
STYLE = "Regular"

PHRASE_PAIRS = (
    ("z", "a"),
    ("a", "y"),
    ("y", "j"),
    ("j", "u"),
    ("D", "i"),
    ("i", "s"),
    ("s", "c"),
    ("c", "o"),
    ("o", "v"),
    ("v", "e"),
    ("e", "r"),
    ("r", "e"),
    ("r", "y"),
    ("y", "w"),
    ("w", "h"),
    ("h", "e"),
    ("e", "v"),
)


def _sample_contour(contour, n_per_cubic: int = 12) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for seg in contour.segments:
        if isinstance(seg, LineSegment):
            if not pts:
                pts.append((seg.p0.x, seg.p0.y))
            pts.append((seg.p1.x, seg.p1.y))
        else:
            assert isinstance(seg, CubicSegment)
            p0, p1, p2, p3 = seg.p0, seg.p1, seg.p2, seg.p3
            if not pts:
                pts.append((p0.x, p0.y))
            for i in range(1, n_per_cubic + 1):
                t = i / n_per_cubic
                u = 1.0 - t
                x = u**3 * p0.x + 3 * u**2 * t * p1.x + 3 * u * t**2 * p2.x + t**3 * p3.x
                y = u**3 * p0.y + 3 * u**2 * t * p1.y + 3 * u * t**2 * p2.y + t**3 * p3.y
                pts.append((x, y))
    return pts



def render_grid_png(
    spaced: dict[str, ComposedGlyph],
    chars: str,
    out_path: Path,
    *,
    cell: int = 140,
    cols: int = 8,
    margin: int = 36,
) -> Path:
    """Filled glyph inventory (avoids OTF even-odd hollow look for proofs)."""
    import math
    rows = math.ceil(len(chars) / cols)
    img = Image.new("RGB", (margin * 2 + cols * cell, margin * 2 + rows * cell + 20), (252, 250, 247))
    draw = ImageDraw.Draw(img)
    draw.text((margin, 8), f"{len(chars)} glyphs", fill=(140, 140, 145))
    for i, ch in enumerate(chars):
        if ch == " " or ch not in spaced:
            continue
        r, c = divmod(i, cols)
        x0 = margin + c * cell
        y0 = margin + 20 + r * cell
        # render glyph into tile
        g = spaced[ch]
        tile = Image.new("L", (cell - 12, cell - 12), 0)
        # reuse sample + winding fill
        from typekernel.geo.contour import signed_area as _sa
        pts_all = []
        polys = []
        for solid in g.solids:
            for contour in solid.contours:
                poly = _sample_contour(contour)
                if len(poly) < 3:
                    continue
                pts_all.extend(poly)
                polys.append((poly, _sa(contour)))
        if not pts_all:
            continue
        xs = [p[0] for p in pts_all]
        ys = [p[1] for p in pts_all]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        tw, th = tile.size
        pad = 10
        sc = min((tw - 2 * pad) / max(maxx - minx, 1), (th - 2 * pad) / max(maxy - miny, 1))
        td = ImageDraw.Draw(tile)
        for poly, area in polys:
            local = [
                (pad + (x - minx) * sc, th - pad - (y - miny) * sc) for x, y in poly
            ]
            td.polygon(local, fill=255 if area >= 0 else 0)
        ink = Image.new("RGB", tile.size, (22, 20, 18))
        cell_img = Image.new("RGB", tile.size, (252, 250, 247))
        cell_img.paste(ink, (0, 0), tile)
        img.paste(cell_img, (x0 + 6, y0 + 6))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def render_phrase_png(
    spaced: dict[str, ComposedGlyph],
    kern: KernTable,
    text: str,
    out_path: Path,
    *,
    px_per_em: float = 72.0,
    margin: int = 48,
) -> Path:
    """Rasterize the brief with winding-aware fills (acceptance specimen)."""
    ctx = next(iter(spaced.values())).context
    scale = px_per_em / ctx.units_per_em
    space_adv = spaced["o"].advance * 0.55

    x = 0.0
    for i, ch in enumerate(text):
        if ch == " ":
            x += space_adv
            continue
        g = spaced[ch]
        if i + 1 < len(text) and text[i + 1] != " " and ch != " ":
            x += g.advance + kern.lookup(ch, text[i + 1])
        else:
            x += g.advance

    width = max(int(x * scale + 2 * margin), 200)
    img_h = int((ctx.ascender - ctx.descender) * scale) + 2 * margin
    baseline = margin + int(ctx.ascender * scale)
    img = Image.new("RGB", (width, img_h), (252, 250, 247))
    mask = Image.new("L", img.size, 0)

    pen_x = float(margin)
    for i, ch in enumerate(text):
        if ch == " ":
            pen_x += space_adv * scale
            continue
        g = spaced[ch]
        polys: list[tuple[list[tuple[float, float]], float]] = []
        for solid in g.solids:
            for contour in solid.contours:
                poly = _sample_contour(contour)
                if len(poly) < 3:
                    continue
                ipoly = [(pen_x + px * scale, baseline - py * scale) for px, py in poly]
                polys.append((ipoly, signed_area(contour)))
        if polys:
            xs = [p[0] for poly, _ in polys for p in poly]
            ys = [p[1] for poly, _ in polys for p in poly]
            bx0, bx1 = int(min(xs)) - 2, int(max(xs)) + 2
            by0, by1 = int(min(ys)) - 2, int(max(ys)) + 2
            tile = Image.new("L", (max(bx1 - bx0, 1), max(by1 - by0, 1)), 0)
            td = ImageDraw.Draw(tile)
            for poly, area in polys:
                local = [(p[0] - bx0, p[1] - by0) for p in poly]
                td.polygon(local, fill=255 if area >= 0 else 0)
            mask.paste(tile, (bx0, by0), tile)
        if i + 1 < len(text) and text[i + 1] != " ":
            pen_x += (g.advance + kern.lookup(ch, text[i + 1])) * scale
        else:
            pen_x += g.advance * scale

    ink = Image.new("RGB", img.size, (22, 20, 18))
    img.paste(ink, (0, 0), mask)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ctx = script_context()
    # Designer order: one glyph at a time + style gate (not phrase-first).
    drawn, style_report = build_charset_sequential(ctx)
    print(
        f"style sequence control={CONTROL_GLYPH} "
        f"order={''.join(DESIGN_ORDER)} "
        f"passed={style_report.passed} "
        f"unlocked={''.join(style_report.unlocked)}"
    )
    if not style_report.passed:
        for rep in style_report.failures:
            bits = ", ".join(
                f"{c.name} Δ={c.delta:.1f}>{c.limit}"
                for c in rep.failures
                if c.delta is not None
            )
            print(f"  FAIL {rep.reference_name}->{rep.candidate_name}: {bits}")
        print("Fix failing glyphs before treating the brief PNG as a design success.")
        return 1
    rhythm = rhythm_from_control_glyphs(drawn["a"], drawn["o"])
    spaced = space_font(drawn, ctx, rhythm=rhythm)
    kern = fit_glyph_pair_kerns(spaced, PHRASE_PAIRS, target=rhythm)

    font = Font.from_context(
        ctx, FAMILY, STYLE, space_width=spaced["o"].advance * 0.55
    )
    font.add_chars(spaced)
    font.add_kern_table(kern)
    font.features = ""

    manifest = build_font(
        font, OUT_DIR, formats=("otf", "ttf"), file_stem="ZayJuLetterScript-Regular"
    )
    otf = manifest.binaries["otf"]
    print("wrote", otf)

    brief = render_phrase_png(
        spaced, kern, BRIEF_SENTENCE, OUT_DIR / "sentence_brief.png", px_per_em=48
    )
    display = render_phrase_png(
        spaced,
        kern,
        BRIEF_SENTENCE,
        OUT_DIR / "sentence_brief_display.png",
        px_per_em=84,
    )
    print("wrote", brief)
    print("wrote", display)

    grid = render_grid_png(spaced, CHARSET, OUT_DIR / "grid.png")
    print("wrote", grid)
    # Also keep FreeType grid for OTF sanity (optional side proof)
    proof_charset_grid(
        otf, OUT_DIR / "grid_otf.png", chars=CHARSET + " ", size=48, cols=8, cell=80
    )

    for ch in ("D", "z", "y", "a", "o"):
        path = OUT_DIR / f"glyph_{ch}.png"
        render_outline_png(spaced[ch].solids[0], path, size=560)
        print("wrote", path)

    worst = None
    for i in range(len(BRIEF_SENTENCE) - 1):
        a, b = BRIEF_SENTENCE[i], BRIEF_SENTENCE[i + 1]
        if a == " " or b == " ":
            continue
        gap = pair_gap_optical(spaced[a], spaced[b], kern=kern.lookup(a, b))
        if worst is None or gap < worst[0]:
            worst = (gap, a, b, kern.lookup(a, b))
    if worst:
        print(f"worst pair: {worst[1]}{worst[2]} gap={worst[0]:.1f} kern={worst[3]:.1f}")

    print("NOTE: Controls sentence_gate does not apply to this skeleton face.")
    print("Style sequence gate passed; brief PNG is a late specimen only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
