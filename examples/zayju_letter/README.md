# 示例：用 typekernel 画一颗受 zayJu 启发的「n」

给**下游字体作者**看的最短路径：改几个参数 → 三次曲线搭轮廓 → 出 PNG / UFO / TTF。

## 跑起来

```bash
# 在 typekernel 仓库根目录
pip install -e ".[dev,specimen,compile]"
python examples/zayju_letter/design_n.py
```

产物在 `out/`：

| 文件 | 说明 |
| --- | --- |
| `n_designed.png` | 设计稿大图 |
| `n_overshoot_pair.png` | 光学 overshoot 前后对比 |
| `ZayJuInspired-Regular.ufo` / `.ttf` | 导出（本地生成，默认不进 git） |

## 用了哪些 API

- `typekernel.geo.PathBuilder` — `moveTo` / `lineTo` / `curveTo` / `closePath`
- `typekernel.optics.apply_overshoot` + `OpticalContext`
- `typekernel.qa.specimen_png.render_outline_png`（需 `pip install -e ".[specimen]"`）
- `typekernel.compile.write_outline_to_ufo` / `build_ttf_from_ufo`

## 设计说明（白话）

比例参考 zayJu Regular（字身高约 540、竖干约 76），但**不是**生产字形拷贝。

有意做了这些，而不是「圆角矩形挖洞」：

- 拱顶略高出字身高，圆肩看起来更稳
- 拱壁比竖干略细一点，带一点对比
- 底脚向外轻轻一撇再落地，软一点

![demo n](../../docs/images/zayju-inspired-n.png)
