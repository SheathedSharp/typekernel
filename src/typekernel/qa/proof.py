"""Render proof sheets from compiled font binaries (OTF/TTF/VF).

Requires the optional ``specimen`` extra (Pillow). Inputs are **paths to font
files** — the same binaries you ship — not live ``Font`` objects.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

__all__ = [
    "DEFAULT_KERN_PAIRS",
    "DEFAULT_SPACING_STRINGS",
    "proof_axis_ladder",
    "proof_charset_grid",
    "proof_context",
    "proof_kern_pairs",
    "proof_labeled_waterfall",
    "proof_sheet",
    "proof_spacing_strings",
    "proof_weight_ladder",
]

DEFAULT_SPACING_STRINGS = ("HHOHH", "nnonn", "OO", "oo", "0123456789")
DEFAULT_KERN_PAIRS = (
    ("T", "o"),
    ("A", "V"),
    ("L", "T"),
    ("r", "o"),
    ("f", "i"),
    ("v", "a"),
    ("T", "y"),
    ("P", "."),
)

_LABEL = (120, 120, 130)
_INK = (22, 22, 26)
_BG = (255, 255, 255)


def _require_pil() -> tuple[Any, Any, Any]:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "proof rendering requires Pillow; install with: pip install -e '.[specimen]'"
        ) from exc
    return Image, ImageDraw, ImageFont


def _fit_line(draw: Any, text: str, font: Any, max_width: float) -> str:
    words = text.split()
    while len(words) > 1 and draw.textlength(" ".join(words), font=font) > max_width:
        words.pop()
    return " ".join(words)


def _save(img: Any, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def proof_context(
    font_path: str | Path,
    text: str,
    out: str | Path,
    *,
    size: int = 36,
    width: int = 1600,
    margin: int = 48,
) -> Path:
    """Single sentence or paragraph at one size (kern on)."""
    Image, ImageDraw, ImageFont = _require_pil()
    face = ImageFont.truetype(str(font_path), size)
    img = Image.new("RGB", (width, margin * 2 + int(size * 1.6)), _BG)
    draw = ImageDraw.Draw(img)
    line = _fit_line(draw, text, face, width - 2 * margin)
    draw.text((margin, margin), line, font=face, fill=_INK, features=["kern"])
    return _save(img, out)


def proof_labeled_waterfall(
    rows: Sequence[tuple[str, str | Path]],
    text: str,
    out: str | Path,
    *,
    sizes: Sequence[int] = (20, 36, 72),
    width: int = 1600,
    margin: int = 48,
    label_w: int = 220,
) -> Path:
    """Several font files (or the same path repeated) at increasing pixel sizes."""
    Image, ImageDraw, ImageFont = _require_pil()
    label_font = ImageFont.load_default(size=16)
    row_h = sum(int(s * 1.5) + 16 for s in sizes) + 24
    img = Image.new("RGB", (width, margin * 2 + row_h * len(rows)), _BG)
    draw = ImageDraw.Draw(img)
    y = margin
    x = margin + label_w
    for label, binary in rows:
        draw.text((margin, y), label, font=label_font, fill=_LABEL)
        for size in sizes:
            face = ImageFont.truetype(str(binary), size)
            line = _fit_line(draw, text, face, width - x - margin)
            draw.text((x, y), line, font=face, fill=_INK, features=["kern"])
            y += int(size * 1.5) + 16
        y += 24
    return _save(img, out)


def proof_axis_ladder(
    font_path: str | Path,
    text: str,
    out: str | Path,
    *,
    axis_values: Sequence[float],
    size: int = 56,
    width: int = 1500,
    margin: int = 40,
    label_w: int = 70,
    label_fmt: str = "{:g}",
) -> Path:
    """Variable font: one line per instance along **axis 0** (fvar order).

    Use for ``wght``, ``opsz``, or any single leading axis. Multi-axis fonts
    still set only the first axis; other axes stay at their default.
    """
    Image, ImageDraw, ImageFont = _require_pil()
    label_font = ImageFont.load_default(size=16)
    values = tuple(axis_values)
    img = Image.new("RGB", (width, margin * 2 + len(values) * int(size * 1.35)), _BG)
    draw = ImageDraw.Draw(img)
    face = ImageFont.truetype(str(font_path), size)
    y = margin
    x = margin + label_w
    for value in values:
        face.set_variation_by_axes([float(value)])
        line = _fit_line(draw, text, face, width - x - margin)
        draw.text(
            (margin, y + size * 0.4),
            label_fmt.format(value),
            font=label_font,
            fill=_LABEL,
        )
        draw.text((x, y), line, font=face, fill=_INK, features=["kern"])
        y += int(size * 1.35)
    return _save(img, out)


def proof_weight_ladder(
    font_path: str | Path,
    text: str,
    out: str | Path,
    *,
    weights: Sequence[int] = (200, 300, 400, 500, 600, 700, 800),
    size: int = 56,
    width: int = 1500,
    margin: int = 40,
    label_w: int = 70,
) -> Path:
    """Variable font: one line per ``wght`` instance (axis 0)."""
    return proof_axis_ladder(
        font_path,
        text,
        out,
        axis_values=tuple(float(w) for w in weights),
        size=size,
        width=width,
        margin=margin,
        label_w=label_w,
        label_fmt="{:.0f}",
    )


def proof_spacing_strings(
    font_path: str | Path,
    out: str | Path,
    *,
    strings: Sequence[str] = DEFAULT_SPACING_STRINGS,
    size: int = 48,
    width: int = 1200,
    margin: int = 40,
    label_w: int = 120,
) -> Path:
    """Sidebearing rhythm checks (``HHOHH``, ``nnonn``, …)."""
    Image, ImageDraw, ImageFont = _require_pil()
    label_font = ImageFont.load_default(size=14)
    row_h = int(size * 1.4) + 12
    img = Image.new("RGB", (width, margin * 2 + row_h * len(strings)), _BG)
    draw = ImageDraw.Draw(img)
    face = ImageFont.truetype(str(font_path), size)
    y = margin
    for s in strings:
        draw.text((margin, y + size * 0.25), s, font=label_font, fill=_LABEL)
        draw.text((margin + label_w, y), s, font=face, fill=_INK)
        y += row_h
    return _save(img, out)


def proof_kern_pairs(
    font_path: str | Path,
    out: str | Path,
    *,
    pairs: Sequence[tuple[str, str]] = DEFAULT_KERN_PAIRS,
    size: int = 72,
    width: int = 1200,
    margin: int = 40,
    gap: int = 48,
) -> Path:
    """Show classic kerning pairs in one row (kern feature on)."""
    Image, ImageDraw, ImageFont = _require_pil()
    face = ImageFont.truetype(str(font_path), size)
    img = Image.new("RGB", (width, margin * 2 + int(size * 1.5)), _BG)
    draw = ImageDraw.Draw(img)
    x = margin
    y = margin
    for left, right in pairs:
        chunk = f"{left}{right}"
        draw.text((x, y), chunk, font=face, fill=_INK, features=["kern"])
        x += draw.textlength(chunk, font=face) + gap
    return _save(img, out)


def _default_charset(font_path: Path) -> str:
    from fontTools.ttLib import TTFont

    tt = TTFont(font_path, lazy=True)
    cmap = tt.getBestCmap() or {}
    chars = sorted(chr(cp) for cp in cmap if cp >= 32 and cp != 0xFFFD)
    tt.close()
    if chars:
        return "".join(chars)
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"


def proof_charset_grid(
    font_path: str | Path,
    out: str | Path,
    *,
    chars: str | None = None,
    size: int = 28,
    cols: int = 16,
    cell: int = 44,
    margin: int = 32,
) -> Path:
    """Glyph inventory from the font cmap (or an explicit string)."""
    Image, ImageDraw, ImageFont = _require_pil()
    font_path = Path(font_path)
    text = chars if chars is not None else _default_charset(font_path)
    rows = (len(text) + cols - 1) // cols
    width = margin * 2 + cols * cell
    height = margin * 2 + rows * cell + 24
    img = Image.new("RGB", (width, height), _BG)
    draw = ImageDraw.Draw(img)
    face = ImageFont.truetype(str(font_path), size)
    label = ImageFont.load_default(size=14)
    draw.text((margin, margin // 2), f"{len(text)} glyphs", font=label, fill=_LABEL)
    y0 = margin + 16
    for i, ch in enumerate(text):
        col = i % cols
        row = i // cols
        cx = margin + col * cell + cell // 2
        cy = y0 + row * cell + cell // 2
        draw.text((cx, cy), ch, font=face, fill=_INK, anchor="mm")
    return _save(img, out)


def proof_sheet(
    font_path: str | Path,
    out: str | Path,
    *,
    context_text: str | None = None,
    spacing_strings: Sequence[str] = DEFAULT_SPACING_STRINGS,
    kern_pairs: Sequence[tuple[str, str]] = DEFAULT_KERN_PAIRS,
    include_grid: bool = True,
    width: int = 1200,
    margin: int = 32,
) -> Path:
    """Stack context, spacing strings, kern pairs, and optional charset grid."""
    Image, _, _ = _require_pil()
    font_path = Path(font_path)
    sections = []

    def _render(fn: Callable[..., Path], *args: Any, **kwargs: Any) -> None:
        tmp = Path(out).with_suffix(".section.png")
        fn(*args, **kwargs, out=tmp)
        pil_image = Image.open(tmp).convert("RGB")
        sections.append(pil_image)
        tmp.unlink(missing_ok=True)

    if context_text:
        _render(proof_context, font_path, context_text, size=32, width=width, margin=margin)
    _render(
        proof_spacing_strings,
        font_path,
        strings=spacing_strings,
        width=width,
        margin=margin,
    )
    _render(proof_kern_pairs, font_path, pairs=kern_pairs, width=width, margin=margin)
    if include_grid:
        _render(proof_charset_grid, font_path, chars=None, margin=margin)

    total_h = sum(im.height for im in sections) + margin * (len(sections) + 1)
    sheet = Image.new("RGB", (max(im.width for im in sections), total_h), _BG)
    y = margin
    for im in sections:
        sheet.paste(im, (0, y))
        y += im.height + margin
    return _save(sheet, out)
