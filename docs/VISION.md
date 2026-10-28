# Vision — typekernel

**一句话**：自建设计 DSL + 光学语义层；编译与 OpenType 表全部复用 [fontTools](https://github.com/fonttools/fonttools)；用 [oh-my-font](https://github.com/SheathedSharp/oh-my-font)（LihuiT / zayJu）当硬狗粮。

> **现行架构与实现路线**：[ARCHITECTURE.md](ARCHITECTURE.md)（第 1–8 节方向，第 9 节交接规格）。本文保留愿景摘要；与 ARCHITECTURE 冲突时以 ARCHITECTURE 为准。

## 要解决什么

「用代码写字体」常常能导出 TTF，却写不出成熟字族——字重靠描边膨胀、三次曲线被采样成折线、斜体靠 shear、没有 overshoot / stem / 对比等光学原语，也没有人眼样张门禁。生态强在**编译**（fontTools / fontmake），弱在**设计判断**。

typekernel 补的是那一层：**可编程的光学与结构内核**，不是又一个编辑器，也不是又一个 fontmake 包装器。

**Coding agent 目标**：让 agent 像人类字体设计师一样，用项目代码写出整族（字重、符号、spacing、特性、proof）。**现行唯一用法**（ARCHITECTURE.md 标准工作流）：

```
tk new → brief.md → system.py → 控制字 → tk proof
      → elements / glyphs → tk audit → corners/ends 插件
      → spacing.py → 母版 → tk build
```

见 [`.agents/skills/typekernel-font-design/`](../.agents/skills/typekernel-font-design/SKILL.md)。不要再走已删除的 `typekernel.parts` / `DesignContext` / yoke 路径。

## 分层（目标架构）

| 层 | 职责 | 本仓 vs 依赖 |
| --- | --- | --- |
| **geo / draw** | 三次曲线一等公民的片段与轮廓 | 自建 |
| **system / project / plugins** | System、@glyph、角点/端点插件 | 自建 |
| **font / compile** | Glyph / Font → UFO / designspace → OT / VF | **fontTools** (+ ufo2ft 等) |

明确**不重造**：OpenType 表、TTX、varLib、feaLib、cu2qu。

## 成功长什么样（方向性）

1. 代码写出的多字重在样张上不像「程序加粗」。
2. 源真相可 diff；字重轴是 designed deltas，不是 stroke expand。
3. Oblique ≠ Italic；视觉回归 + 人类批样是默认 DX。
4. 社区能指出：这是「设计层」拼图，不是编译包装。

## 完整计划

详细调研、缺口分析、分层落地顺序与交接规格见 [ARCHITECTURE.md](ARCHITECTURE.md)。本仓以该文为准。

## 状态

**geo / draw / system / project / plugins / cli / starters/latin_sans** 已按 ARCHITECTURE.md 交接规格落地。字母几何在 starter 项目里；内核无 letter builders。`typekernel.parts` / `DesignContext` / FormSources / yoke 已删除。

**Italic / 第二套 starter（skeleton+pen）** 已以 `latin-humanist-italic` 落地；不要用机械 oblique 冒充 Italic。见 [ARCHITECTURE.md](ARCHITECTURE.md) 第 6 节与 [dev-standards.md](dev-standards.md)。
