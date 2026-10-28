"""``tk pen`` — preview elliptical broad-nib effective width by stroke direction."""

from __future__ import annotations

import math
from pathlib import Path

from typekernel.geo.stroke import Pen

__all__ = ["render_pen_preview"]


def render_pen_preview(
    *,
    contrast: float = 0.55,
    angle_deg: float = 30.0,
    thickness: float = 100.0,
    out: str | Path = "pen_preview.png",
) -> Path:
    """Draw stroke-direction samples so agents see which way the pen thickens.

    ``Pen.contrast`` is the ellipse axis ratio (not a vertical/horizontal stem
    ratio by itself). Effective width depends on the stroke direction relative
    to ``angle_deg``.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "tk pen requires Pillow; install with: pip install -e '.[specimen]'"
        ) from exc

    pen = Pen(thickness=float(thickness), contrast=float(contrast), angle_deg=float(angle_deg))
    width, height = 900, 520
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=16)
        font_sm = ImageFont.load_default(size=13)
    except TypeError:  # older Pillow
        font = ImageFont.load_default()
        font_sm = font

    title = (
        f"Pen thickness={thickness:g}  contrast={contrast:g}  angle={angle_deg:g}°  "
        "(contrast = ellipse axis ratio)"
    )
    draw.text((24, 16), title, fill=(30, 30, 34), font=font)

    cx, cy = 200, 280
    # Pen ellipse at origin for reference
    rx, ry = pen.rx, pen.ry
    rad = math.radians(angle_deg)
    # Sample ellipse boundary in pen space, rotate by angle
    pts = []
    for i in range(64):
        t = 2 * math.pi * i / 64
        x, y = rx * math.cos(t), ry * math.sin(t)
        xr = x * math.cos(rad) - y * math.sin(rad)
        yr = x * math.sin(rad) + y * math.cos(rad)
        pts.append((cx + xr * 1.6, cy - yr * 1.6))
    draw.polygon(pts, outline=(40, 40, 48), fill=(230, 230, 236))
    draw.text((cx - 40, cy + ry * 1.6 + 12), "pen ellipse", fill=(90, 90, 100), font=font_sm)

    # Direction rows
    x0, y0 = 420, 70
    draw.text((x0, y0 - 28), "stroke dir → effective width", fill=(30, 30, 34), font=font)
    for i, deg in enumerate(range(0, 180, 15)):
        theta = math.radians(deg + 90.0)  # normal
        nx, ny = math.cos(theta), math.sin(theta)
        w = 2.0 * pen.half_width(nx, ny)
        y = y0 + i * 34
        # stroke sample line
        L = 70
        sx = x0 + 20
        sy = y + 10
        dx = math.cos(math.radians(deg)) * L
        dy = -math.sin(math.radians(deg)) * L
        # thickness as short perpendicular bar
        half = w * 0.35
        px, py = -math.sin(math.radians(deg)) * half, -math.cos(math.radians(deg)) * half
        poly = [
            (sx - dx * 0.1 + px, sy - dy * 0.1 + py),
            (sx + dx + px, sy + dy + py),
            (sx + dx - px, sy + dy - py),
            (sx - dx * 0.1 - px, sy - dy * 0.1 - py),
        ]
        draw.polygon(poly, fill=(32, 32, 38))
        draw.text(
            (x0 + 160, y),
            f"{deg:3d}°  →  {w:5.1f} du",
            fill=(30, 30, 34),
            font=font_sm,
        )

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path
