# Vision — typekernel

**一句话**：自建设计 DSL + 光学语义层；编译与 OpenType 表全部复用 [fontTools](https://github.com/fonttools/fonttools)；用 [oh-my-font](https://github.com/SheathedSharp/oh-my-font)（LihuiT / zayJu）当硬狗粮。

## 要解决什么

「用代码写字体」常常能导出 TTF，却写不出成熟字族——字重靠描边膨胀、三次曲线被采样成折线、斜体靠 shear、没有 overshoot / stem / 对比等光学原语，也没有人眼样张门禁。生态强在**编译**（fontTools / fontmake），弱在**设计判断**。

typekernel 补的是那一层：**可编程的光学与结构内核**，不是又一个编辑器，也不是又一个 fontmake 包装器。

## 分层（目标架构）

| 层 | 职责 | 本仓 vs 依赖 |
| --- | --- | --- |
| **geo-kernel** | 三次曲线一等公民的几何核 | 自建 |
| **type-semantics** | overshoot、stem、对比、接合、designed deltas | 自建 |
| **compile** | UFO / designspace → OT 表 / VF | **fontTools** (+ ufo2ft / fontmake 等) |

明确**不重造**：OpenType 表、TTX、varLib、feaLib、cu2qu。

## 成功长什么样（方向性）

1. 代码写出的多字重在样张上不像「程序加粗」。
2. 源真相可 diff；字重轴是 designed deltas，不是 stroke expand。
3. Oblique ≠ Italic；视觉回归 + 人类批样是默认 DX。
4. 社区能指出：这是「设计层」拼图，不是编译包装。

## 完整计划

详细调研、缺口分析与 12 个月路线图写在独立规划文档里（作者本地 / 工作区：`font-from-code-foundation-plan.md`）。本仓只保留这份愿景摘要；计划定稿后可链到仓库 `docs/` 或外部 URL。

## 状态

**Scaffolding.** 无设计 API、无几何实现。先立仓与许可证，再按计划落地 geo-kernel。
