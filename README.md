# typekernel

**用代码写成熟字族的光学 / 设计语义内核** — optical design-semantics kernel for fonts-as-code.  
Depends on [fontTools](https://github.com/fonttools/fonttools); **does not** rebuild OpenType tables.

> 自建设计层，编译层坐在 fontTools 上。不是编辑器，不是又一个 fontmake 包装器。

## 是什么 / 不是什么

| 是 | 不是 |
| --- | --- |
| 可编程的几何核 + 光学原语（overshoot、stem、对比、接合） | Glyphs / FontForge 式 GUI |
| 字重 / 轴作为 **designed deltas** 的语义层 | 「描边膨胀 = 字重」的脚本合集 |
| 导出到 UFO / designspace，再经 fontTools 编译 | 重造 OT 表、TTX、varLib、feaLib |
| 日后给 [oh-my-font](https://github.com/SheathedSharp/oh-my-font)（LihuiT / zayJu）与其他项目复用的地基 | 成品字族发行仓 |

## 分层（目标）

```
geo-kernel  →  type-semantics  →  compile (fontTools / UFO / designspace)
三次曲线核      光学与字族轴语义      OT 表与二进制：不重造，只依赖
```

## 状态

**Scaffolding（脚手架）.** 包名与仓库骨架已立，尚无设计 API。版本 `0.0.0`。

完整产品 / 技术规划见独立文档（作者工作区）：`font-from-code-foundation-plan.md`（定稿后可迁入本仓 `docs/` 或外链）。愿景摘要：[docs/VISION.md](docs/VISION.md)。

## 安装（占位）

```bash
# 尚未发布到 PyPI；本地可编辑安装：
pip install -e ".[dev]"
```

需要 Python ≥ 3.11；运行时依赖 `fonttools`。

## 贡献

仓库刚起步。欢迎先读 [docs/VISION.md](docs/VISION.md) 对齐目标；实现与 PR 约定将在有第一块 geo-kernel 后补上。Issue / PR 模板与行为准则后续再加。

## 许可

[MIT](LICENSE) © 2026 zayju
