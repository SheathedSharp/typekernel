# 示例：用 typekernel 零件组装「zayju」

不参考 zayJu，参考 Anthropic 一类**几何新无衬线**的气质。五个字母共用一个
`DesignContext`（字干、对比、overshoot、字距），用 Stem / Bowl / Bar / Hook 等
零件组装 — 像 Three.js 用简单几何体搭复杂物体，而不是每个字母手写一整段贝塞尔。

## 三栏分别是什么

| 栏 | 内容 |
| --- | --- |
| 苹果系统默认 | macOS `SFNS.ttf`（SF Pro / System Font） |
| Anthropic | 官网 CDN 上的 **Anthropic Sans**（专有字体，脚本临时下载到 `/tmp`，**不进仓库**） |
| typekernel 零件组装 | `typekernel.parts` + `word_zayju()` 画出的几何无衬线 |

## 重新出图

在仓库根目录：

```bash
pip install -e ".[specimen,boolean]"
pip install brotli          # 仅中间栏：woff2 → 可渲染
python examples/anthropic_zayju/design_zayju.py
```

`boolean` extra（skia-pathops）用于把重叠的零件并成一条干净外轮廓，避免接缝缺口。

产物：

- `out/compare.png` — 三栏对比
- `docs/images/zayju-apple-anthropic-typekernel.png` — 同上（给文档用）
- `out/zayju_typekernel.png` / `out/letter_*.png` — 二创单字与整词

## 设计说明（白话）

- **一个上下文**：五个字母共享 stem / contrast / overshoot / tracking
- **零件**：竖干、横杠、碗+字怀、斜干、钩、点；字母 = 零件组合 + 可选并集
- **a**：单层几何（碗 + 右干），不是双眼 a
- **仍是演示**：字怀完成度、字偶间距、与 Anthropic 的细部仍有差距

这是演示「用代码组字」好不好用，不是生产字库。
