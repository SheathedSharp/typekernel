"""Contact sheets and comparison renders for full charset review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typekernel.geo.outline import Outline
from typekernel.parts.compose import ComposedGlyph
from typekernel.parts.context import DesignContext
from typekernel.parts.family import Controls

__all__ = [
    "contact_sheet",
    "diff_overlay",
    "review_index",
    "weight_ladder_sheet",
]

_DEFAULT_LADDER_CHARS = "Hamburgefonstiv &!?#$"
_DEFAULT_LADDER_STEMS = (50.0, 70.0, 110.0, 150.0)


def _require_pil() -> tuple[Any, Any, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise ImportError(
            "sheet rendering requires Pillow; install with: pip install -e '.[specimen]'"
        ) from exc
    return Image, ImageDraw, ImageFont


def _glyph_outline(glyph: ComposedGlyph) -> Outline:
    contours = tuple(
        contour for outline in (*glyph.solids, *glyph.holes) for contour in outline.contours
    )
    return Outline(contours)


def _zone_lines(ctx: DesignContext, cell_h: int, margin: int) -> list[tuple[int, str]]:
    """Horizontal lines (y, label) in cell coordinates, Y-down."""
    scale = (cell_h - 2 * margin) / max(ctx.ascender - ctx.descender, 1.0)

    def y_for(design_y: float) -> int:
        return int(margin + (ctx.ascender - design_y) * scale)

    return [
        (y_for(0.0), "base"),
        (y_for(ctx.x_height), "xh"),
        (y_for(ctx.cap_height), "cap"),
        (y_for(ctx.ascender), "asc"),
        (y_for(ctx.descender), "desc"),
    ]


def contact_sheet(
    controls: Controls,
    out: str | Path,
    *,
    chars: str | None = None,
    cell: int = 56,
    glyph_size: int = 72,
    max_width: int = 1600,
    zones: bool = True,
) -> Path:
    """Grid of every glyph with labels; width capped for agent preview."""
    from typekernel.qa.specimen_png import render_outline_png

    Image, ImageDraw, ImageFont = _require_pil()
    charset = chars if chars is not None else controls.supported
    ctx = controls.context
    drawn = controls.build_all(charset)
    label_h = 14
    row_h = cell + label_h
    cols = max(1, max_width // cell)
    rows = (len(charset) + cols - 1) // cols
    width = min(max_width, cols * cell)
    height = rows * row_h + 8
    sheet = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    zone_lines = _zone_lines(ctx, cell, 6) if zones else []

    for index, ch in enumerate(charset):
        row, col = divmod(index, cols)
        x0, y0 = col * cell, row * row_h + 4
        tmp = Path(out).parent / f"_contact_{index}.png"
        render_outline_png(_glyph_outline(drawn[ch]), tmp, size=glyph_size)
        tile = Image.open(tmp).convert("RGB")
        tile = tile.resize((cell - 4, cell - 4))
        sheet.paste(tile, (x0 + 2, y0 + 2))
        tmp.unlink(missing_ok=True)
        if zones:
            for y, _ in zone_lines:
                yy = y0 + 2 + min(y, cell - 6)
                draw.line([(x0 + 2, yy), (x0 + cell - 2, yy)], fill=(220, 220, 230), width=1)
        label = ch if ch.isprintable() and ch != " " else "·"
        draw.text((x0 + 2, y0 + cell - 2), label, fill=(80, 80, 90), font=font)

    destination = Path(out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination)
    return destination


def weight_ladder_sheet(
    preset: DesignContext,
    out: str | Path,
    *,
    chars: str = _DEFAULT_LADDER_CHARS,
    stems: tuple[float, ...] = _DEFAULT_LADDER_STEMS,
    size: int = 48,
) -> Path:
    """Same snippet at increasing stem values (counter collapse check)."""
    from typekernel.compile import FamilyBuildOptions, build_font, compose_font_from_controls

    Image, ImageDraw, ImageFont = _require_pil()
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = out_path.parent / "_ladder_tmp"
    tmp_dir.mkdir(exist_ok=True)
    font = ImageFont.load_default()
    row_h = size + 28
    width = 1500
    height = row_h * len(stems) + 8
    sheet = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(sheet)

    for row, stem in enumerate(stems):
        ctx = preset.tuned(stem=float(stem))
        controls = Controls.from_context(ctx)
        if stem >= 110.0:
            controls = controls.with_stem_relief()
        built = compose_font_from_controls(
            controls,
            "Ladder",
            options=FamilyBuildOptions(chars=chars, liga=False),
        )
        result = build_font(built, tmp_dir, formats=("otf",))
        otf = result.binaries["otf"]
        face = ImageFont.truetype(str(otf), size)
        y = row * row_h + 4
        draw.text((8, y + size // 2), f"stem={int(stem)}", fill=(120, 120, 130), font=font)
        draw.text((120, y), chars, font=face, fill=(20, 20, 24))

    sheet.save(out_path)
    for p in tmp_dir.glob("*"):
        p.unlink(missing_ok=True)
    tmp_dir.rmdir()
    return out_path


def diff_overlay(
    trial: Controls,
    baseline: Controls,
    out: str | Path,
    *,
    chars: str = "mutj&#!$",
    size: int = 128,
) -> Path:
    """Red = trial, blue = baseline outlines for quick shape diff."""
    from typekernel.qa.specimen_png import render_outline_png

    Image, _, _ = _require_pil()
    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    trial_g = trial.build_all(chars)
    base_g = baseline.build_all(chars)
    cell = size + 16
    cols = len(chars)
    sheet = Image.new("RGBA", (cols * cell, cell), (255, 255, 255, 255))

    for index, ch in enumerate(chars):
        t_tmp = out_path.parent / f"_diff_t_{index}.png"
        b_tmp = out_path.parent / f"_diff_b_{index}.png"
        render_outline_png(
            _glyph_outline(trial_g[ch]),
            t_tmp,
            size=size,
            foreground=(200, 48, 48, 180),
        )
        render_outline_png(
            _glyph_outline(base_g[ch]),
            b_tmp,
            size=size,
            foreground=(48, 96, 200, 180),
        )
        t_im = Image.open(t_tmp).convert("RGBA")
        b_im = Image.open(b_tmp).convert("RGBA")
        tile = Image.alpha_composite(b_im, t_im)
        sheet.paste(tile, (index * cell + 8, 8), tile)
        t_tmp.unlink(missing_ok=True)
        b_tmp.unlink(missing_ok=True)

    sheet.convert("RGB").save(out_path)
    return out_path


def review_index(out_dir: str | Path, paths: dict[str, Path]) -> Path:
    """Write ``index.json`` listing review artifact paths."""
    destination = Path(out_dir) / "index.json"
    payload = {key: str(path) for key, path in sorted(paths.items())}
    payload["family_gate_version"] = "1"
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
