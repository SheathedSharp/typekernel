"""Render an outline to a PNG specimen for human preview.

**Preview only.** Cubics remain the design truth. This module samples Bézier
curves into polylines solely so Pillow can draw pixels — the samples are never
written back into an ``Outline`` and must not be treated as geometry.

Requires the optional ``specimen`` extra::

    pip install -e ".[specimen]"

Generate the synthetic O demo::

    python -m typekernel.qa.specimen_png
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from typekernel.geo.outline import Outline, bounds
from typekernel.geo.point import Point
from typekernel.geo.segment import CubicSegment, LineSegment

# Samples per cubic for preview rasterization — not design resolution.
_CUBIC_SAMPLES = 32
_DEFAULT_MARGIN = 0.08
_BG = (250, 250, 248, 255)
_FG = (32, 32, 36, 255)

PixelTransform = Callable[[Point], tuple[float, float]]


def render_outline_png(
    outline: Outline,
    path: str | Path,
    size: int = 512,
    *,
    margin_fraction: float = _DEFAULT_MARGIN,
    background: tuple[int, int, int, int] = _BG,
    foreground: tuple[int, int, int, int] = _FG,
    supersample: int = 4,
) -> Path:
    """Draw ``outline`` into a square PNG at ``path``.

    Font Y-up coordinates are flipped for image Y-down. Closed contours are
    filled; when more than one closed contour is present, the first is treated
    as the outer shape and later closed contours punch holes (so a ring ``O``
    shows its counter). Open contours are stroked.

    Anti-aliasing: the shape is rasterized at ``size * supersample`` then
    downsampled with Lanczos. Cubics remain the design truth — sampling is
    preview-only. Set ``supersample=1`` for the old nearest-edge look.

    Raises:
        ImportError: if Pillow is not installed.
        ValueError: if ``size`` / ``supersample`` is not positive.
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover - exercised when extra missing
        raise ImportError(
            "render_outline_png requires Pillow; install with: pip install -e '.[specimen]'"
        ) from exc

    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    if supersample <= 0:
        raise ValueError(f"supersample must be positive, got {supersample}")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    min_x, min_y, max_x, max_y = bounds(outline)
    width = max_x - min_x
    height = max_y - min_y
    if width <= 0 or height <= 0:
        image = Image.new("RGBA", (size, size), background)
        image.save(destination, format="PNG")
        return destination

    render_size = size * supersample
    margin = margin_fraction * render_size
    drawable = render_size - 2 * margin
    scale = drawable / max(width, height)
    offset_x = margin + (drawable - width * scale) / 2.0
    offset_y = margin + (drawable - height * scale) / 2.0

    def to_pixel(point: Point) -> tuple[float, float]:
        px = offset_x + (point.x - min_x) * scale
        py = offset_y + (max_y - point.y) * scale
        return (px, py)

    image = Image.new("RGBA", (render_size, render_size), background)
    mask = Image.new("L", (render_size, render_size), 0)
    mask_draw = ImageDraw.Draw(mask)

    closed_polys: list[list[tuple[float, float]]] = []
    open_polylines: list[list[tuple[float, float]]] = []

    # More cubic samples when supersampling so curves stay smooth after downsample.
    samples = _CUBIC_SAMPLES * max(1, supersample // 2)

    for contour in outline.contours:
        if not contour.segments:
            continue
        poly = _sample_contour(contour.segments, to_pixel, samples=samples)
        if len(poly) < 2:
            continue
        if contour.closed:
            closed_polys.append(poly)
        else:
            open_polylines.append(poly)

    for index, poly in enumerate(closed_polys):
        fill_value = 255 if index == 0 else 0
        mask_draw.polygon(poly, fill=fill_value)

    ink = Image.new("RGBA", (render_size, render_size), foreground)
    image = Image.composite(ink, image, mask)

    draw = ImageDraw.Draw(image)
    for poly in open_polylines:
        if len(poly) >= 2:
            draw.line(poly, fill=foreground, width=max(1, render_size // 256))

    if supersample > 1:
        image = image.resize((size, size), resample=Image.Resampling.LANCZOS)

    image.save(destination, format="PNG")
    return destination


def _sample_contour(
    segments: tuple[LineSegment | CubicSegment, ...],
    to_pixel: PixelTransform,
    *,
    samples: int = _CUBIC_SAMPLES,
) -> list[tuple[float, float]]:
    """Sample contour segments into a pixel-space polyline (preview only)."""
    points: list[tuple[float, float]] = []
    if not segments:
        return points
    n = max(1, samples)
    first = segments[0].points[0]
    points.append(to_pixel(first))
    for segment in segments:
        if isinstance(segment, LineSegment):
            points.append(to_pixel(segment.p1))
        else:
            for sample_index in range(1, n + 1):
                t = sample_index / n
                point = _eval_cubic(segment.p0, segment.p1, segment.p2, segment.p3, t)
                points.append(to_pixel(point))
    return points


def _eval_cubic(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    """Evaluate a cubic Bézier at ``t`` in [0, 1] (preview sampling only)."""
    u = 1.0 - t
    x = (
        u * u * u * p0.x
        + 3.0 * u * u * t * p1.x
        + 3.0 * u * t * t * p2.x
        + t * t * t * p3.x
    )
    y = (
        u * u * u * p0.y
        + 3.0 * u * u * t * p1.y
        + 3.0 * u * t * t * p2.y
        + t * t * t * p3.y
    )
    return Point(x, y)


def _default_fixture_path() -> Path:
    """Locate ``tests/fixtures/synthetic_O.json`` from a source checkout."""
    # src/typekernel/qa/specimen_png.py → repo root is parents[3]
    root = Path(__file__).resolve().parents[3]
    return root / "tests" / "fixtures" / "synthetic_O.json"


def main(argv: list[str] | None = None) -> int:
    """CLI: write a synthetic-O PNG specimen (and optional overshoot pair)."""
    import argparse

    from typekernel.geo.fixtures import load_synthetic_outline
    from typekernel.optics.context import OpticalContext
    from typekernel.optics.overshoot import apply_overshoot

    parser = argparse.ArgumentParser(
        description=(
            "Render a synthetic O PNG specimen (preview only; cubic remains truth)."
        )
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("artifacts/specimens/synthetic_O.png"),
        help="Output PNG path (default: artifacts/specimens/synthetic_O.png)",
    )
    parser.add_argument("--size", type=int, default=512, help="Square pixel size")
    parser.add_argument(
        "--with-overshoot",
        action="store_true",
        help="Also write a side-by-side before/after overshoot PNG next to -o",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="Path to synthetic_O.json (default: tests/fixtures/synthetic_O.json)",
    )
    args = parser.parse_args(argv)

    fixture = args.fixture if args.fixture is not None else _default_fixture_path()
    outline = load_synthetic_outline(fixture)
    out = render_outline_png(outline, args.output, size=args.size)
    print(f"wrote {out}")

    if args.with_overshoot:
        from PIL import Image

        after = apply_overshoot(outline, OpticalContext(overshoot_round=12.0), kind="round")
        before_path = args.output.with_name(args.output.stem + "_before.png")
        after_path = args.output.with_name(args.output.stem + "_after_overshoot.png")
        pair_path = args.output.with_name(args.output.stem + "_overshoot_pair.png")
        render_outline_png(outline, before_path, size=args.size)
        render_outline_png(after, after_path, size=args.size)
        left = Image.open(before_path).convert("RGBA")
        right = Image.open(after_path).convert("RGBA")
        gap = 16
        pair = Image.new("RGBA", (left.width * 2 + gap, left.height), _BG)
        pair.paste(left, (0, 0))
        pair.paste(right, (left.width + gap, 0))
        pair.save(pair_path, format="PNG")
        print(f"wrote {before_path}")
        print(f"wrote {after_path}")
        print(f"wrote {pair_path}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
