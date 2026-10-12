# typekernel

**用代码写成熟字族的光学 / 设计语义内核** — optical design-semantics kernel for fonts-as-code.  
Depends on [fontTools](https://github.com/fonttools/fonttools); **does not** rebuild OpenType tables.

> 自建设计层，编译层坐在 fontTools 上。不是编辑器，不是又一个 fontmake 包装器。

## 一眼看懂

![typekernel 概览：几何、光学、字重](docs/images/what-typekernel-does.jpg)

*几何 → 光学外扩 → 字重用点位移（不是涂粗）。*

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

版本仍是 `0.0.0`。已落地：

- **几何核**（`typekernel.geo`）— 三次曲线轮廓、路径构建、笔桥
- **光学原语**（`typekernel.optics`）— overshoot 等（合成 O 标本已过人审）
- **字重 / 轴**（`typekernel.axes`）— `WeightDelta`、masters、`.designspace` 导出（点位移，不是涂粗）

下一步：**编译桥** — 把轮廓写成 UFO，再经 fontTools / fontmake 产出字体文件。

愿景摘要：[docs/VISION.md](docs/VISION.md)。开发约定：[docs/dev-standards.md](docs/dev-standards.md)。

## 安装（占位）

```bash
# 尚未发布到 PyPI；本地可编辑安装：
pip install -e ".[dev]"
```

需要 Python ≥ 3.11；运行时依赖 `fonttools`。

## 文档

| Doc | 内容 |
| --- | --- |
| [docs/VISION.md](docs/VISION.md) | 产品愿景 |
| [docs/dev-standards.md](docs/dev-standards.md) | 提交信息、typing、几何原则、公开 API 纪律 |
| [docs/notes/fonttools-reuse.md](docs/notes/fonttools-reuse.md) | fontTools / pathops 复用对照 |
| [approvals/geo-public-api.json](approvals/geo-public-api.json) | Geo 公开 API 人审记录 |
| [approvals/optical-overshoot.json](approvals/optical-overshoot.json) | Overshoot 人审记录 |

## 贡献

先读 [docs/VISION.md](docs/VISION.md) 与 [docs/dev-standards.md](docs/dev-standards.md)。
合并前跑通 `pytest -q`、`ruff check src tests`、`mypy -p typekernel`。
Issue / PR 模板与行为准则后续再加。

## 许可

[MIT](LICENSE) © 2026 zayju
