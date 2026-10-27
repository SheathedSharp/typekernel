# typekernel

**用代码写成熟字族的光学 / 设计语义内核** — optical design-semantics kernel for fonts-as-code.  
Depends on [fontTools](https://github.com/fonttools/fonttools); **does not** rebuild OpenType tables.

> 自建设计层，编译层坐在 fontTools 上。不是编辑器，不是又一个 fontmake 包装器。

> **架构入口（现行）**：[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 三层分离、M0–M6 路线与交接规格。实现与评审以该文为准。

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

## 分层（现行）

```
geo / draw  →  system / project / plugins  →  font / compile (fontTools)
片段与轮廓        System + @glyph + 角点/端点插件      Glyph / Font → UFO / OTF / VF
```

旧的 `typekernel.parts` / `DesignContext` 字母 API 已在 M4 删除。字母几何写在**项目**里（starter），不进内核。

## 状态

版本仍是 `0.0.0`。已落地：

- **几何核**（`typekernel.geo`）— 三次曲线轮廓、路径构建、笔桥
- **绘图**（`typekernel.draw`）— `Writer` / `Fragment` / `Drawing`、角点槽、overlap 构造
- **System / Project**（`typekernel.system` / `typekernel.project`）— 设计数值表、`@glyph`、母版求值
- **插件**（`typekernel.plugins`）— corners / ends / passes（plain、overshoot、diagonal_comp…）
- **光学原语**（`typekernel.optics`）— overshoot、stem 测量、光学间距
- **字体模型**（`typekernel.font`）— `Font` / `Glyph` / kerning；从 `System` 推度量
- **CLI** — `tk new` / `tk build` / `tk proof` / `tk audit`
- **Starter** — `latin-sans`（a–z A–Z 0–9 + 标点 + spacing + Light/Bold VF）

## 做一个能安装的字体

按 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) **§4** 工作流：

```bash
pip install -e ".[compile,specimen]"
tk new myface --starter latin-sans
cd myface
# 改 system.py → 看控制字 → 扩字组 → tk audit → spacing.py → 母版 →
tk build .
tk proof control .
tk audit .
```

Coding agent 技能：[`.agents/skills/typekernel-font-design/`](.agents/skills/typekernel-font-design/SKILL.md)。

最小可跑示例：[`examples/latin_sans_quickstart/`](examples/latin_sans_quickstart/)（脚手架 + 出 OTF + 控制样张）。  
Geo 层示范（不经 starter）：[`examples/zayju_letter/`](examples/zayju_letter/)。

```python
# 项目内（tk new 之后）：system.py + glyphs/*.py + font.py
# 不要再 from typekernel.parts import DesignContext
from typekernel.cli.build import build_project
from typekernel.cli.new import create_project

root = create_project("demo", parent="/tmp", starter="latin-sans")
font, result = build_project(root, formats=("otf",))
print(result.binaries["otf"])
```

**校样**（`typekernel.qa.proof`）— 从编译后的字体路径排瀑布、间距串、字偶对与字符网格。

Agent 试验记录：[`docs/AGENT_TRIALS.md`](docs/AGENT_TRIALS.md)。  
历史开发计划（含 §8）：[`docs/DEVELOPMENT_PLAN.md`](docs/DEVELOPMENT_PLAN.md)。

## 开发

见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) §9 与 [docs/dev-standards.md](docs/dev-standards.md)。本地：

```bash
pytest -q
```
