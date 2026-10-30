"""Edit / context / overlay / diff views for ``tk see`` (target §6.2)."""

from __future__ import annotations

import itertools
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from typekernel.draw.drawing import on_curve_at
from typekernel.geo.outline import bounds
from typekernel.geo.segment import CubicSegment, LineSegment
from typekernel.perceive.explain import explain
from typekernel.perceive.render import LiveGlyph, flatten_outline, render_live, simplify_outline
from typekernel.perceive.sidecar import write_sidecar
from typekernel.project.session import ProjectSession
from typekernel.qa.outline_hash import outline_hash
from typekernel.system.table import System

__all__ = [
    "SeeResult",
    "context_view",
    "diff_view",
    "edit_view",
    "overlay_view",
    "reference_view",
    "skeleton_view",
]


@dataclass
class SeeResult:
    """PNG path plus sidecar path produced by a view."""

    png: Path
    sidecar: Path
    meta: dict[str, Any] = field(default_factory=dict)


def _system_for(session: ProjectSession, master: str | None) -> System:
    system: System = session.project.system
    if master is not None:
        by = {m.name: m for m in session.project.masters}
        if master in by:
            system = by[master].system
    return system


def _frame(
    outline_bounds: tuple[float, float, float, float],
    system: System,
    *,
    size: int,
    margin_fraction: float = 0.12,
) -> tuple[float, float, float, float, float]:
    """Return ``(min_x, min_y, scale, offset_x, offset_y)`` for Y-up → image."""
    bx0, by0, bx1, by1 = outline_bounds
    # Include zone lines in the frame.
    min_x = min(bx0, -system.stem.get("lc", 80.0))
    max_x = max(bx1, bx1 + 20.0)
    min_y = min(by0, system.zones.desc - abs(system.overshoot.round))
    max_y = max(by1, system.zones.asc + abs(system.overshoot.round))
    width = max(max_x - min_x, 1.0)
    height = max(max_y - min_y, 1.0)
    margin = margin_fraction * size
    drawable = size - 2 * margin
    scale = drawable / max(width, height)
    offset_x = margin + (drawable - width * scale) / 2.0
    offset_y = margin + (drawable - height * scale) / 2.0
    return (min_x, max_y, scale, offset_x, offset_y)


def _to_px(
    x: float,
    y: float,
    *,
    min_x: float,
    max_y: float,
    scale: float,
    offset_x: float,
    offset_y: float,
) -> tuple[float, float]:
    return (offset_x + (x - min_x) * scale, offset_y + (max_y - y) * scale)


def edit_view(
    session: ProjectSession,
    glyph: str,
    *,
    master: str | None = None,
    size: int = 512,
    out: Path | str | None = None,
) -> SeeResult:
    """Edit view: fill + outline + nodes + handles + labels + zones + measures."""
    from PIL import Image, ImageDraw, ImageFont

    draft = session.evaluate(glyph, master=master, slots=True)
    g = session.glyph(glyph, master=master)
    drawing = draft.drawing
    system = _system_for(session, master)
    report = explain(session, glyph, master=master)

    try:
        ob = bounds(g.outline)
    except ValueError:
        ob = (0.0, 0.0, float(g.advance), system.zones.x)

    min_x, max_y, scale, ox, oy = _frame(ob, system, size=size)

    def px(x: float, y: float) -> tuple[float, float]:
        return _to_px(x, y, min_x=min_x, max_y=max_y, scale=scale, offset_x=ox, offset_y=oy)

    img = Image.new("RGBA", (size, size), (250, 250, 248, 255))
    from PIL import ImageChops

    mask = Image.new("L", (size, size), 0)
    try:
        simp = simplify_outline(g.outline)
    except (ValueError, RuntimeError, TypeError):
        simp = g.outline
    chord = max(0.25, 0.5 / max(scale, 1e-9))
    for poly in flatten_outline(simp, chord_budget=chord):
        pix = [px(x, y) for x, y in poly]
        layer = Image.new("L", (size, size), 0)
        ImageDraw.Draw(layer).polygon(pix, fill=255)
        mask = ImageChops.difference(mask, layer)
    soft = Image.new("RGBA", (size, size), (160, 175, 200, 100))
    img.paste(soft, mask=mask)

    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=11)
        font_sm = ImageFont.load_default(size=9)
    except TypeError:
        font = ImageFont.load_default()
        font_sm = font

    # Zone lines + labels.
    zones = {
        "base": system.zones.base,
        "x-height": system.zones.x,
        "cap": system.zones.cap,
        "asc": system.zones.asc,
        "desc": system.zones.desc,
    }
    zone_colors = {
        "base": (120, 120, 120, 180),
        "x-height": (80, 120, 180, 180),
        "cap": (80, 80, 160, 160),
        "asc": (60, 140, 60, 160),
        "desc": (160, 80, 60, 160),
    }
    x0 = px(min_x - 50, 0)[0]
    x1 = px(ob[2] + 80, 0)[0]
    for name, y in zones.items():
        ypx = px(0, y)[1]
        draw.line([(x0, ypx), (x1, ypx)], fill=zone_colors[name], width=1)
        draw.text((4, ypx - 10), name, fill=zone_colors[name], font=font_sm)

    # Contour strokes + cubic handles.
    for contour in drawing.contours:
        for segment in contour.segments:
            if isinstance(segment, LineSegment):
                draw.line([px(segment.p0.x, segment.p0.y), px(segment.p1.x, segment.p1.y)],
                          fill=(40, 40, 48, 255), width=2)
            else:
                assert isinstance(segment, CubicSegment)
                # Flatten lightly for stroke.
                from typekernel.geo.stroke import CubicBezier, _flatten_cubic_segment

                pts: list[tuple[float, float]] = []
                max_err = [0.0]
                bez = CubicBezier(
                    (segment.p0.x, segment.p0.y),
                    (segment.p1.x, segment.p1.y),
                    (segment.p2.x, segment.p2.y),
                    (segment.p3.x, segment.p3.y),
                )
                _flatten_cubic_segment(bez, chord, pts, max_err)
                if len(pts) >= 2:
                    draw.line([px(x, y) for x, y in pts], fill=(40, 40, 48, 255), width=2)
                # Handles
                h0 = px(segment.p0.x, segment.p0.y)
                h1 = px(segment.p1.x, segment.p1.y)
                h2 = px(segment.p2.x, segment.p2.y)
                h3 = px(segment.p3.x, segment.p3.y)
                draw.line([h0, h1], fill=(200, 140, 60, 160), width=1)
                draw.line([h3, h2], fill=(200, 140, 60, 160), width=1)
                for hx, hy in (h1, h2):
                    draw.ellipse([hx - 2, hy - 2, hx + 2, hy + 2], fill=(200, 140, 60, 200))

    # Nodes: square = corner, circle = smooth; labels.
    node_table: list[dict[str, Any]] = []
    for ci, (contour, cnodes) in enumerate(zip(drawing.contours, drawing.nodes, strict=True)):
        for node in cnodes:
            pt = on_curve_at(contour, node.index)
            cx, cy = px(pt.x, pt.y)
            smooth = bool(node.meta.get("smooth", 0.0)) if node.meta else False
            r = 4
            if smooth:
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(20, 20, 30, 255), width=2)
            else:
                draw.rectangle([cx - r, cy - r, cx + r, cy + r], outline=(20, 20, 30, 255), width=2)
            if node.tag:
                draw.text((cx + 5, cy - 10), node.tag, fill=(30, 30, 40, 220), font=font_sm)
            node_table.append(
                {"tag": node.tag, "pos_x": pt.x, "pos_y": pt.y, "contour": ci, "smooth": smooth}
            )

    # Sidebearings / advance.
    draw.line([px(0, system.zones.desc), px(0, system.zones.asc)], fill=(220, 80, 80, 160), width=1)
    draw.line(
        [px(g.advance, system.zones.desc), px(g.advance, system.zones.asc)],
        fill=(220, 80, 80, 160),
        width=1,
    )
    draw.text(px(g.advance / 2, system.zones.desc - 20), f"adv={g.advance:.0f}", fill=(180, 60, 60, 200), font=font_sm)

    # Measure annotations.
    measure_rows: list[dict[str, Any]] = []
    for m in report.measures:
        measure_rows.append(
            {
                "kind": m.kind,
                "from_tag": m.a,
                "to_tag": m.b,
                "expected": m.expected,
                "measured": m.measured,
            }
        )
        if m.measured is None or m.b is None:
            continue
        try:
            pa = drawing.point(m.a)
            pb = drawing.point(m.b)
        except KeyError:
            continue
        draw.line([px(pa.x, pa.y), px(pb.x, pb.y)], fill=(40, 140, 90, 180), width=1)
        mx, my = px((pa.x + pb.x) / 2, (pa.y + pb.y) / 2)
        label = f"{m.kind}:{m.measured:.1f}"
        if m.expected is not None:
            label += f"/{m.expected:.1f}"
        draw.text((mx, my), label, fill=(20, 100, 60, 220), font=font_sm)

    out_path = Path(out) if out else Path(f"see-{glyph}.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")

    meta: dict[str, Any] = {
        "view": "edit",
        "glyph": glyph,
        "master": master,
        "glyphs": [glyph],
        "outline_hashes": {glyph: outline_hash(g.outline)},
        "size": size,
        "nodes": node_table,
        "measures": measure_rows,
        "Measure": measure_rows,
        "labels": [n["tag"] for n in node_table if n["tag"]],
        "topology": {
            "counters": report.counters,
            "islands": report.islands,
            "slit_counters": report.slit_counters,
        },
        "advance": g.advance,
        "lsb": report.lsb,
        "rsb": report.rsb,
        "bbox": list(report.bbox),
    }
    side = write_sidecar(out_path, meta)
    return SeeResult(png=out_path, sidecar=side, meta=meta)


def _context_refs(session: ProjectSession, glyph: str) -> list[str]:
    """Pick reference glyphs by shared traits (no hardcoded letter names)."""
    specs = session.specs()
    spec = specs.get(glyph)
    if spec is None:
        return []
    traits = set(spec.traits)
    # Prefer refs that share vertical-band traits.
    band = traits & {"x-height", "cap", "ascender", "descender", "figure"}
    scored: list[tuple[int, str]] = []
    for name, other in specs.items():
        if name == glyph:
            continue
        ot = set(other.traits)
        score = len(band & ot) * 10 + len(traits & ot)
        if score <= 0:
            continue
        # Prefer shorter names / control-ish groups.
        if other.group.startswith("control") or "control" in other.group:
            score += 5
        scored.append((score, name))
    scored.sort(key=lambda t: (-t[0], t[1]))
    refs = [n for _, n in scored[:4]]
    return refs


def context_view(
    session: ProjectSession,
    glyph: str,
    *,
    master: str | None = None,
    size: int = 512,
    out: Path | str | None = None,
) -> SeeResult:
    """Context strips: ref+ref+glyph+ref+ref at three sizes."""
    from PIL import Image, ImageDraw, ImageFont

    refs = _context_refs(session, glyph)
    if not refs:
        # Fall back to repeating the glyph itself.
        refs = [glyph]
    patterns = []
    for ref in refs[:2]:
        patterns.append([ref, ref, glyph, ref, ref])

    system = _system_for(session, master)
    img = Image.new("RGBA", (size, size), (250, 250, 248, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default(size=12)
    except TypeError:
        font = ImageFont.load_default()

    row_h = size // max(1, len(patterns) * 3)
    y = 8
    rendered_rows: list[dict[str, Any]] = []
    for pattern in patterns:
        for px_size in (48, 72, 96):
            run: list[LiveGlyph] = []
            names: list[str] = []
            for name in pattern:
                g = session.glyph(name, master=master)
                run.append(LiveGlyph(g.outline, advance=g.advance))
                names.append(name)
            strip = render_live(run, size=max(px_size * 4, 128), supersample=2, margin_fraction=0.05)
            assert isinstance(strip, Image.Image)
            # Fit strip into row.
            target_h = max(24, row_h - 16)
            ratio = target_h / strip.height
            tw = max(1, int(strip.width * ratio))
            th = max(1, int(strip.height * ratio))
            strip = strip.resize((tw, th))
            x = 8
            img.paste(strip, (x, y), strip)
            draw.text((x, y + th + 1), " ".join(names) + f" @{px_size}", fill=(60, 60, 70), font=font)
            rendered_rows.append({"names": names, "px": px_size})
            y += row_h
            if y >= size - 8:
                break
        if y >= size - 8:
            break

    out_path = Path(out) if out else Path(f"see-{glyph}-context.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    g = session.glyph(glyph, master=master)
    meta = {
        "view": "context",
        "glyph": glyph,
        "master": master,
        "glyphs": [glyph, *refs],
        "outline_hashes": {glyph: outline_hash(g.outline)},
        "rows": rendered_rows,
        "zones_x": system.zones.x,
    }
    side = write_sidecar(out_path, meta)
    return SeeResult(png=out_path, sidecar=side, meta=meta)


def overlay_view(
    session: ProjectSession,
    glyph: str,
    *,
    masters: Sequence[str] | None = None,
    size: int = 512,
    out: Path | str | None = None,
) -> SeeResult:
    """Overlay masters with node correspondence lines."""
    from PIL import Image, ImageDraw

    master_names = list(masters) if masters else [m.name for m in session.project.masters]
    if not master_names:
        master_names = [None]

    colors = [
        (40, 90, 180, 200),
        (180, 60, 60, 200),
        (40, 140, 70, 200),
        (160, 100, 40, 200),
    ]
    system = _system_for(session, master_names[0] if master_names else None)
    # Frame from first master.
    g0 = session.glyph(glyph, master=master_names[0] if master_names else None)
    try:
        ob = bounds(g0.outline)
    except ValueError:
        ob = (0.0, 0.0, float(g0.advance), system.zones.x)
    min_x, max_y, scale, ox, oy = _frame(ob, system, size=size)

    def px(x: float, y: float) -> tuple[float, float]:
        return _to_px(x, y, min_x=min_x, max_y=max_y, scale=scale, offset_x=ox, offset_y=oy)

    img = Image.new("RGBA", (size, size), (250, 250, 248, 255))
    draw = ImageDraw.Draw(img)
    node_sets: list[dict[str, tuple[float, float]]] = []
    hashes: dict[str, str] = {}

    for i, master in enumerate(master_names):
        color = colors[i % len(colors)]
        draft = session.evaluate(glyph, master=master, slots=True)
        g = session.glyph(glyph, master=master)
        hashes[str(master)] = outline_hash(g.outline)
        chord = max(0.25, 0.5 / max(scale, 1e-9))
        for poly in flatten_outline(g.outline, chord_budget=chord):
            pix = [px(x, y) for x, y in poly]
            if len(pix) >= 2:
                draw.line(pix + [pix[0]], fill=color, width=2)
        tagged: dict[str, tuple[float, float]] = {}
        for contour, cnodes in zip(draft.drawing.contours, draft.drawing.nodes, strict=True):
            for node in cnodes:
                if not node.tag:
                    continue
                pt = on_curve_at(contour, node.index)
                tagged[node.tag] = (pt.x, pt.y)
                cx, cy = px(pt.x, pt.y)
                draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=color)
        node_sets.append(tagged)

    # Correspondence lines between consecutive masters.
    if len(node_sets) >= 2:
        for a, b in itertools.pairwise(node_sets):
            for tag, (x1, y1) in a.items():
                if tag not in b:
                    continue
                x2, y2 = b[tag]
                draw.line([px(x1, y1), px(x2, y2)], fill=(120, 120, 120, 140), width=1)

    out_path = Path(out) if out else Path(f"see-{glyph}-overlay.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    meta = {
        "view": "overlay",
        "glyph": glyph,
        "masters": [str(m) for m in master_names],
        "outline_hashes": hashes,
        "glyphs": [glyph],
    }
    side = write_sidecar(out_path, meta)
    return SeeResult(png=out_path, sidecar=side, meta=meta)


def diff_view(
    session: ProjectSession,
    glyph: str,
    *,
    against: Mapping[str, str] | Path | str | None = None,
    master: str | None = None,
    size: int = 512,
    out: Path | str | None = None,
) -> SeeResult:
    """Before/after: red = removed ink, green = added (vs snapshot hashes or prior outline)."""
    import json

    from PIL import Image, ImageChops

    g = session.glyph(glyph, master=master)
    current = render_live(
        [LiveGlyph(g.outline, advance=g.advance)],
        size=size,
        supersample=2,
        margin_fraction=0.1,
        foreground=(0, 0, 0, 255),
        background=(255, 255, 255, 255),
    )
    assert isinstance(current, Image.Image)
    current_mask = current.convert("L").point(lambda v: 255 if v < 200 else 0)

    baseline_outline = None
    baseline_hash = None
    if against is None:
        snap = Path(session.root) / "build" / "glyph_hashes.json"
        against = snap if snap.is_file() else None
    if isinstance(against, (str, Path)):
        path = Path(against)
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            glyphs = data.get("glyphs", data)
            baseline_hash = glyphs.get(glyph)
    elif isinstance(against, Mapping):
        baseline_hash = against.get(glyph)

    # Without a stored outline we can only flag hash change; render empty baseline.
    baseline_mask = Image.new("L", (size, size), 0)
    if baseline_outline is not None:
        base_img = render_live(
            [LiveGlyph(baseline_outline, advance=g.advance)],
            size=size,
            supersample=2,
            margin_fraction=0.1,
            foreground=(0, 0, 0, 255),
            background=(255, 255, 255, 255),
        )
        assert isinstance(base_img, Image.Image)
        baseline_mask = base_img.convert("L").point(lambda v: 255 if v < 200 else 0)

    added = ImageChops.subtract(current_mask, baseline_mask)
    removed = ImageChops.subtract(baseline_mask, current_mask)
    img = Image.new("RGBA", (size, size), (250, 250, 248, 255))
    img.paste(Image.new("RGBA", (size, size), (40, 40, 48, 80)), mask=current_mask)
    img.paste(Image.new("RGBA", (size, size), (40, 180, 80, 200)), mask=added)
    img.paste(Image.new("RGBA", (size, size), (200, 50, 50, 200)), mask=removed)

    out_path = Path(out) if out else Path(f"see-{glyph}-diff.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    cur_hash = outline_hash(g.outline)
    meta = {
        "view": "diff",
        "glyph": glyph,
        "master": master,
        "outline_hashes": {glyph: cur_hash},
        "baseline_hash": baseline_hash,
        "changed": baseline_hash is not None and baseline_hash != cur_hash,
        "glyphs": [glyph],
    }
    side = write_sidecar(out_path, meta)
    return SeeResult(png=out_path, sidecar=side, meta=meta)


def reference_view(
    session: ProjectSession,
    glyph: str,
    *,
    reference: Path | str,
    master: str | None = None,
    size: int = 512,
    out: Path | str | None = None,
) -> SeeResult:
    """Side-by-side with a reference OTF/TTF (look-only; D4)."""
    from PIL import Image, ImageDraw, ImageFont

    ref_path = Path(reference)
    if not ref_path.is_file():
        raise FileNotFoundError(ref_path)

    g = session.glyph(glyph, master=master)
    left = render_live(
        [LiveGlyph(g.outline, advance=g.advance)],
        size=size,
        supersample=2,
        margin_fraction=0.12,
    )
    assert isinstance(left, Image.Image)

    img = Image.new("RGBA", (size * 2, size), (250, 250, 248, 255))
    img.paste(left, (0, 0))
    draw = ImageDraw.Draw(img)
    try:
        face = ImageFont.truetype(str(ref_path), size=int(size * 0.55))
    except OSError as exc:
        raise ValueError(f"cannot open reference font {ref_path}: {exc}") from exc
    # Map unicode if available.
    ch = None
    if g.unicodes:
        ch = chr(g.unicodes[0])
    if ch:
        draw.text((size + size // 8, size // 6), ch, font=face, fill=(32, 32, 36, 255))
    try:
        font = ImageFont.load_default(size=14)
    except TypeError:
        font = ImageFont.load_default()
    draw.text((8, 8), "live", fill=(60, 60, 70), font=font)
    draw.text((size + 8, 8), f"ref:{ref_path.name}", fill=(60, 60, 70), font=font)

    out_path = Path(out) if out else Path(f"see-{glyph}-reference.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG")
    meta = {
        "view": "reference",
        "glyph": glyph,
        "master": master,
        "reference": str(ref_path),
        "outline_hashes": {glyph: outline_hash(g.outline)},
        "glyphs": [glyph],
    }
    side = write_sidecar(out_path, meta)
    return SeeResult(png=out_path, sidecar=side, meta=meta)


def skeleton_view(
    session: ProjectSession,
    glyph: str,
    *,
    master: str | None = None,
    size: int = 512,
    out: Path | str | None = None,
) -> SeeResult:
    """S4 skeleton view: midline (when present), node indices, curvature comb."""
    import math

    from PIL import Image, ImageDraw, ImageFont

    draft = session.evaluate(glyph, master=master, slots=True)
    g = session.glyph(glyph, master=master)
    drawing = draft.drawing
    system = _system_for(session, master)

    try:
        ob = bounds(g.outline)
    except ValueError:
        ob = (0.0, 0.0, float(g.advance), system.zones.x)

    min_x, max_y, scale, ox, oy = _frame(ob, system, size=size)

    def px(x: float, y: float) -> tuple[float, float]:
        return _to_px(x, y, min_x=min_x, max_y=max_y, scale=scale, offset_x=ox, offset_y=oy)

    img = Image.new("RGBA", (size, size), (252, 252, 250, 255))
    draw = ImageDraw.Draw(img)
    try:
        font_sm = ImageFont.load_default(size=9)
    except TypeError:
        font_sm = ImageFont.load_default()

    # Faint outline.
    chord = max(0.25, 0.5 / max(scale, 1e-9))
    try:
        simp = simplify_outline(g.outline)
    except (ValueError, RuntimeError, TypeError):
        simp = g.outline
    for poly in flatten_outline(simp, chord_budget=chord):
        if len(poly) >= 2:
            draw.line([px(x, y) for x, y in poly], fill=(200, 200, 205, 220), width=1)

    # Midline from GlyphDraft.skeleton when feasible.
    skeleton = getattr(draft, "skeleton", None)
    mid_pts: list[tuple[float, float]] = []
    if skeleton is not None:
        segs = getattr(skeleton, "segments", None)
        if segs is not None:
            from typekernel.geo.stroke import CubicCenterline, flatten_cubic_centerline

            flat, _rep = flatten_cubic_centerline(
                CubicCenterline(tuple(segs), closed=bool(getattr(skeleton, "closed", False))),
                chord_budget=1.0,
            )
            mid_pts = [(float(x), float(y)) for x, y in flat.points]
        else:
            pts = getattr(skeleton, "points", None)
            if pts is not None:
                mid_pts = [(float(x), float(y)) for x, y in pts]
    if len(mid_pts) >= 2:
        draw.line([px(x, y) for x, y in mid_pts], fill=(220, 60, 80, 255), width=2)

    # Node indices + curvature comb on outline cubics.
    node_i = 0
    for contour in drawing.contours:
        for segment in contour.segments:
            if isinstance(segment, LineSegment):
                p0 = px(segment.p0.x, segment.p0.y)
                draw.ellipse([p0[0] - 2, p0[1] - 2, p0[0] + 2, p0[1] + 2], fill=(40, 40, 50, 255))
                draw.text((p0[0] + 3, p0[1] - 8), str(node_i), fill=(40, 40, 50, 200), font=font_sm)
                node_i += 1
                continue
            assert isinstance(segment, CubicSegment)
            # Curvature comb: sample κ ≈ |x'y'' - y'x''| / (x'²+y'²)^(3/2)
            for t in (0.2, 0.4, 0.6, 0.8):
                mt = 1.0 - t
                # Position
                x = (
                    mt**3 * segment.p0.x
                    + 3 * mt**2 * t * segment.p1.x
                    + 3 * mt * t**2 * segment.p2.x
                    + t**3 * segment.p3.x
                )
                y = (
                    mt**3 * segment.p0.y
                    + 3 * mt**2 * t * segment.p1.y
                    + 3 * mt * t**2 * segment.p2.y
                    + t**3 * segment.p3.y
                )
                # First derivative
                dx = (
                    3 * mt**2 * (segment.p1.x - segment.p0.x)
                    + 6 * mt * t * (segment.p2.x - segment.p1.x)
                    + 3 * t**2 * (segment.p3.x - segment.p2.x)
                )
                dy = (
                    3 * mt**2 * (segment.p1.y - segment.p0.y)
                    + 6 * mt * t * (segment.p2.y - segment.p1.y)
                    + 3 * t**2 * (segment.p3.y - segment.p2.y)
                )
                # Second derivative
                ddx = (
                    6 * mt * (segment.p2.x - 2 * segment.p1.x + segment.p0.x)
                    + 6 * t * (segment.p3.x - 2 * segment.p2.x + segment.p1.x)
                )
                ddy = (
                    6 * mt * (segment.p2.y - 2 * segment.p1.y + segment.p0.y)
                    + 6 * t * (segment.p3.y - 2 * segment.p2.y + segment.p1.y)
                )
                speed2 = dx * dx + dy * dy
                if speed2 < 1e-8:
                    continue
                kappa = abs(dx * ddy - dy * ddx) / (speed2**1.5)
                ln = math.hypot(dx, dy)
                nx, ny = -dy / ln, dx / ln
                comb = min(40.0, kappa * 4000.0)
                a = px(x, y)
                b = px(x + nx * comb, y + ny * comb)
                draw.line([a, b], fill=(80, 140, 200, 200), width=1)
            p0 = px(segment.p0.x, segment.p0.y)
            draw.ellipse([p0[0] - 2, p0[1] - 2, p0[0] + 2, p0[1] + 2], fill=(40, 40, 50, 255))
            draw.text((p0[0] + 3, p0[1] - 8), str(node_i), fill=(40, 40, 50, 200), font=font_sm)
            node_i += 1

    out_path = Path(out) if out else Path(f"see-{glyph}-skeleton.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    side = write_sidecar(
        out_path,
        {
            "view": "skeleton",
            "glyph": glyph,
            "master": master,
            "has_midline": bool(len(mid_pts) >= 2),
            "outline_hash": outline_hash(g.outline),
        },
    )
    return SeeResult(png=out_path, sidecar=side, meta={"has_midline": len(mid_pts) >= 2})
