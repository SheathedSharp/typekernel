"""用 typekernel 画一颗受 zayJu 启发的小写 n（示范下游怎么用库）。

这不是 oh-my-font 生产字形的拷贝，而是：
- 参考 zayJu Regular 的大致比例（字身高、字干、圆软底脚）
- 用三次曲线亲手搭外轮廓（不是中线描边膨胀）
- 顺带试用光学 overshoot、样品 PNG、以及 UFO/TTF 导出

运行（在仓库根目录，已 editable 安装 typekernel）::

    python examples/zayju_letter/design_n.py
"""

from __future__ import annotations

from pathlib import Path

from typekernel.compile import build_ttf_from_ufo, write_outline_to_ufo
from typekernel.geo import Outline, PathBuilder
from typekernel.geo.outline import bounds
from typekernel.optics import OpticalContext, apply_overshoot
from typekernel.qa.specimen_png import render_outline_png

# ---------------------------------------------------------------------------
# 设计参数（受 zayJu Regular 启发——改这几行就能调气质）
# ---------------------------------------------------------------------------
X_HEIGHT = 540.0
STEM = 76.0
LEFT = 32.0
RIGHT = 642.0
ADVANCE = 674

R_SHOULDER = 155.0  # 外肩
R_COUNTER = 88.0  # 字怀上角
FOOT_FLARE = 22.0  # 底脚相对字干再向外撇
FOOT_ROUND = 64.0  # 底脚转弯半径
ARCH_LIFT = 12.0  # 拱顶相对字身高多探出
ARCH_THIN = 0.86  # 拱壁相对竖干略细
OVERSHOOT = 8.0

K = 0.5523

OUT_DIR = Path(__file__).resolve().parent / "out"


def design_n() -> Outline:
    """一笔闭合的小写 n：竖干直立、底脚外撇圆润、圆肩微拱。"""
    b = PathBuilder()

    arch = STEM * ARCH_THIN
    y0 = 0.0
    y_top = X_HEIGHT + ARCH_LIFT
    y_inner = y_top - arch

    x_lo, x_li = LEFT, LEFT + STEM
    x_ri, x_ro = RIGHT - STEM, RIGHT
    # 底脚外撇后的左右最外点
    x_flo = x_lo - FOOT_FLARE
    x_fro = x_ro + FOOT_FLARE

    rs, rc = R_SHOULDER, R_COUNTER
    fr = FOOT_ROUND
    # 内脚圆角略小；平底段要保证不交叉
    fi = min(fr * 0.75, STEM * 0.45)

    # --- 从左干外缘、底脚以上起笔，先上肩再下到右脚，再进字怀 ---
    # 左干外缘（直立）从脚上沿开始
    b.moveTo(x_lo, fr)
    b.lineTo(x_lo, y_top - rs)
    # 左外肩
    b.curveTo(x_lo, y_top - rs + K * rs, x_lo + rs - K * rs, y_top, x_lo + rs, y_top)
    # 拱顶微拱
    b.curveTo(x_lo + rs + 95, y_top + 6, x_ro - rs - 95, y_top + 6, x_ro - rs, y_top)
    # 右外肩
    b.curveTo(x_ro - rs + K * rs, y_top, x_ro, y_top - rs + K * rs, x_ro, y_top - rs)
    b.lineTo(x_ro, fr)

    # 右底脚：先外撇，再落地，再收到内缘
    # 外撇：从 (x_ro, fr) 弯到 (x_fro, y0+一小段) 再到底
    b.curveTo(x_ro, fr - K * fr * 0.5, x_fro - FOOT_FLARE * 0.2, y0 + fr * 0.35, x_fro, y0 + fr * 0.15)
    b.curveTo(x_fro, y0 + fr * 0.15 - K * (fr * 0.15), x_fro - fr * 0.5, y0, x_fro - fr * 0.55, y0)
    b.lineTo(x_ri + fi, y0)
    b.curveTo(x_ri + fi - K * fi, y0, x_ri, fi - K * fi, x_ri, fi)

    # 右干内 → 字怀
    b.lineTo(x_ri, y_inner - rc)
    b.curveTo(
        x_ri, y_inner - rc + K * rc, x_ri - rc + K * rc, y_inner, x_ri - rc, y_inner
    )
    b.lineTo(x_li + rc, y_inner)
    b.curveTo(
        x_li + rc - K * rc, y_inner, x_li, y_inner - rc + K * rc, x_li, y_inner - rc
    )
    b.lineTo(x_li, fi)

    # 左底脚：内缘落地 → 外撇 → 回到左干外缘
    b.curveTo(x_li, fi - K * fi, x_li - fi + K * fi, y0, x_li - fi, y0)
    b.lineTo(x_flo + fr * 0.55, y0)
    b.curveTo(
        x_flo + fr * 0.55 - K * (fr * 0.5),
        y0,
        x_flo,
        y0 + fr * 0.15 - K * (fr * 0.15),
        x_flo,
        y0 + fr * 0.15,
    )
    b.curveTo(
        x_flo + FOOT_FLARE * 0.2,
        y0 + fr * 0.35,
        x_lo,
        fr - K * fr * 0.5,
        x_lo,
        fr,
    )

    b.closePath()
    return b.build()


def _write_pair(before: Outline, after: Outline, path: Path, size: int = 512) -> Path:
    from PIL import Image

    left_p = path.with_name(path.stem + "_L.png")
    right_p = path.with_name(path.stem + "_R.png")
    render_outline_png(before, left_p, size=size)
    render_outline_png(after, right_p, size=size)
    left = Image.open(left_p).convert("RGBA")
    right = Image.open(right_p).convert("RGBA")
    gap = 20
    pair = Image.new("RGBA", (left.width * 2 + gap, left.height), (250, 250, 248, 255))
    pair.paste(left, (0, 0))
    pair.paste(right, (left.width + gap, 0))
    pair.save(path)
    left_p.unlink(missing_ok=True)
    right_p.unlink(missing_ok=True)
    return path


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outline = design_n()
    print("bounds", bounds(outline))

    big = OUT_DIR / "n_designed.png"
    render_outline_png(outline, big, size=720)
    print("wrote", big)

    ctx = OpticalContext(
        units_per_em=1000.0,
        x_height=X_HEIGHT,
        cap_height=730.0,
        overshoot_round=OVERSHOOT,
        overshoot_sharp=0.0,
    )
    after = apply_overshoot(outline, ctx, kind="round")
    pair = _write_pair(outline, after, OUT_DIR / "n_overshoot_pair.png")
    print("wrote", pair)
    print("after overshoot bounds", bounds(after))

    ufo_path = OUT_DIR / "ZayJuInspired-Regular.ufo"
    if ufo_path.exists():
        import shutil

        shutil.rmtree(ufo_path)
    ufo = write_outline_to_ufo(
        outline,
        ufo_path,
        glyph_name="n",
        units_per_em=1000,
        advance_width=ADVANCE,
        family_name="ZayJuInspiredDemo",
        style_name="Regular",
    )
    print("wrote", ufo)
    ttf = OUT_DIR / "ZayJuInspired-Regular.ttf"
    manifest = build_ttf_from_ufo(
        ufo, ttf, manifest_path=OUT_DIR / "build-manifest.json"
    )
    print("wrote", ttf, "ufo2ft", manifest.ufo2ft_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
