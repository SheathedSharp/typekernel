# 示例：用 typekernel 二创「zayju」

不参考 zayJu，参考 Anthropic 一类**几何新无衬线**的气质，用手写 `PathBuilder` 轮廓拼出 `z a y j u`，再和两种现成字体并排对比。

## 三栏分别是什么

| 栏 | 内容 |
| --- | --- |
| 苹果系统默认 | macOS `SFNS.ttf`（SF Pro / System Font） |
| Anthropic | 官网 CDN 上的 **Anthropic Sans**（专有字体，脚本临时下载到 `/tmp`，**不进仓库**） |
| typekernel 二创 | 本目录 `design_zayju.py` 里用库画的几何无衬线 |

## 重新出图

在仓库根目录：

```bash
pip install -e ".[specimen]"
pip install brotli          # 仅中间栏：woff2 → 可渲染
python examples/anthropic_zayju/design_zayju.py
```

产物：

- `out/compare.png` — 三栏对比
- `docs/images/zayju-apple-anthropic-typekernel.png` — 同上（给文档用）
- `out/zayju_typekernel.png` / `out/letter_*.png` — 二创单字与整词

## 二创设计说明（白话）

- **字干匀**：多数笔画像一根等宽管子（中线描边或显式外轮廓）
- **a**：几何单层（圆碗 + 右干），不是双眼 a，也不是 zayJu 软底脚
- **y / z**：斜笔终端偏平切
- **j**：方点 + 左钩
- **u**：双直干 + 底弯，带一点 overshoot

这是演示「用代码写字」好不好用，不是生产字库。
