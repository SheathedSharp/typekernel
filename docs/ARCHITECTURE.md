# typekernel 架构与实现路径

> 第一性原理：**人类字体设计师怎么做，coding agent 用 typekernel 时就怎么做。**
> 库只提供“设计师的工具”，不提供“一副已经设计好的字”。

本文是方向文件。它规定什么该进内核、什么该做成插件、什么属于用户的字体项目，以及从当前代码迁过去的顺序。和本文冲突的旧文档（`AGENT_GOAL.md`、skill 里的 yoke 教学、`.agents/01-architecture.md`）以本文为准，迁移期内逐步改写。

---

## 1. 诊断：现在为什么走偏

### 1.1 库在替设计师画字，agent 只剩拧旋钮

现在的主路径是：

```
DesignContext(20 个旋钮) → n_metrics(ctx) 用经验公式推出 n 的几何
  → build_n / h_from_n / m_from_n / … / A_from_H / eight_from_O
  → 结构有缝 → seal / soften / relieve / blend 补丁
```

证据（2026-10 主干）：

| 现象 | 数据 |
| --- | --- |
| 字形真相写死在库函数里 | `parts/control.py` 4082 行、`parts/caps.py` 3628 行、`punctuation.py` 1362 行、`diagonals.py` 949 行 |
| 风格维度在每个字母里交叉分支 | `style.serif` 147 处（7 个文件）、斜体判断 44 处、`vf_compat` 56 处 |
| 单个“零件”就是整字 + 开关 | `shoulder_yoke` 14 个参数，内部按 serif × italic × is_h × vf_compat 分支 |
| 几何来自中心公式，不来自设计决定 | `counter = x_height * (0.46 + 0.12 * aperture)`、`join_y = x_height * (0.50 + 0.04 * roundness)` |
| 模块之间互相借私有函数 | `caps`/`figures`/`punctuation`/`diagonals` 从 `control` 等处导入 27 个 `_` 开头的私有符号 |
| 连接处靠事后修补 | `blend/seal/soften/relieve/heal` 107 处；近 40 个提交里大量 “seal hairline / relieve counter / equalize diagonals” |
| 测试锁死的是“库自带那副字” | 80 个测试文件直接调用 `build_n` / `*_from_n` / `*_yoke` / 预设；`tests/parts` 546 个用例；外加 golden outline hash |

后果：

1. **组合爆炸。** 每加一个风格维度（墨阱、球形端点、宽度轴），所有字母函数都要再加一层分支。这就是“厚组合”。
2. **agent 拿不到所有权。** agent 想改 `h` 的胯部深度，只能找一个恰好暴露出来的参数；找不到就只能改库。之前的试字会话结论就是“同一套 n/o 拓扑上拧 preset，不是新造型”。
3. **补丁不收敛。** 接合处的形状不是被画出来的，而是被焊出来的，所以每次换字重、换风格都会裂出新缝，再加新补丁。
4. **测试测错了对象。** 现在的测试在验收一副具体的字（这个预设、这三档 stem 下的分段数是否一致），而不是验收工具是否可靠。设计师从不靠“锁定轮廓哈希”判断一个字好不好。

### 1.2 根因

当前代码把三件不同的东西揉在了一起：

| 应该分开的东西 | 现在在哪 |
| --- | --- |
| **工具**：画轮廓、量尺寸、挂衬线、做光学修正、排间距、编译、出样张 | `geo`、`optics`、`compile`、`qa`（大体正确） |
| **设计知识**：肩怎么起、碗怎么接干、斜笔怎么补偿 | 散在 `parts` 的私有函数里，跟具体字母绑死 |
| **一副具体的字**（“库自带的那副无衬线”） | `parts.control` / `caps` / `diagonals` / `figures` / `punctuation` / `glyph_specs` / `family` |

第三类本应是**示例或模板**，现在却是库的公共 API，并且整个测试体系都围着它转。

---

## 2. 第一性原理：人类设计师的流程和工具

### 2.1 流程

1. **Brief**：用途、字重范围、衬线与否、构造方式（几何 / 宽头笔 / 尖头笔 / 刻写）。
2. **定系统**：UPM、对齐区（基线 / x 高 / 大写高 / 升部 / 降部）、各类 stem 值、横竖对比、超调量。这是一张**设计师亲手定的数值表**，不是从五个旋钮推出来的。
3. **画控制字**：`n o H O`，常再加 `a e g s` 这类“性格字”。每个字都是**直接画**出来的。
4. **在字串里测**：`nnonoo`、`HHOHOO`、`hamburgefonstiv`，看节奏和灰度，回去改。
5. **扩字组**：把 `n` 的肩**复制**到 `m h r`，把 `o` 的碗**复制**到 `b d p q`，然后**逐个字做光学调整**（`b` 的碗不等于 `o`：更窄、接干处要削薄）。复用靠显式复制元素，调整留在本字。
6. **间距**：以 `n`/`o`（`H`/`O`）为基准定侧距（Tracy 法 / metrics keys），再做字偶。
7. **母版**：每个字重单独设计极端母版，**刻意保证点结构一致**，再插值检查。
8. **斜体**：另一套设计，不是倾斜变换。
9. **出厂**：命名、特性、hinting、导出；重叠在静态字体导出时去除，可变字体可保留。

### 2.2 设计软件（Glyphs / RoboFont）给设计师的工具

| 工具 | 含义 | 对 typekernel 的启示 |
| --- | --- | --- |
| 点 / 路径直接编辑 | 每个字的轮廓归设计师所有 | 每个字形是用户项目里的一段**自己的代码** |
| 字体级 stems、对齐区、guides | 系统是数据表 | `System` 只存数值，不含几何推导公式 |
| Components | 整字引用（`é = e + ´`） | 已有，保留 |
| **Corner components** | 衬线挂在**轮廓的角点**上 | 衬线做成插件，按**命名角点**挂载，字母代码不知道衬线是什么形状 |
| **Cap components** | 端点形状挂在**笔画的开口端** | 端点（平切 / 斜切 / 球 / 喇叭）做成插件，按**命名开口端**挂载 |
| 复制粘贴元素 | 肩、碗在字之间复用 | 项目里的 `elements.py`，字形显式 import，本地可覆盖 |
| 量尺、stem 测量 | 随时测量和系统比对 | 审计工具，按命名节点测量 |
| 文本预览 | 在字串里看 | 样张是主要的“测试” |
| 母版兼容检查 | 点结构一致才可插值 | 用节点标签 + 段结构做兼容检查 |

**结论：设计师的“可组合性”来自三处——系统数值表、可复制的元素、挂在角点 / 端点上的组件。** 没有任何一个“中心字”推导全世界，也没有事后焊缝。

---

## 3. 目标架构

### 3.1 三层分离

```
┌─────────────────────────────────────────────────────────────────┐
│  字体项目（用户 / agent 拥有）   typekernel new myfont           │
│  brief.md  system.py  elements.py  glyphs/*.py  spacing.py      │
│  masters.py  font.py  proofs/                                    │
│  ← starter 模板“拷贝进来”（shadcn 模式），之后完全归 agent 改     │
└───────────────────────────────▲─────────────────────────────────┘
                                │ 只调用公开 API
┌───────────────────────────────┴─────────────────────────────────┐
│  插件（可选、互相独立、按协议实现）                              │
│  corners: slab / bracketed / wedge / ink_trap / rounded          │
│  ends:    flat / angled / ball / flare / teardrop                │
│  passes:  overshoot / diagonal_comp / crotch_thin / contrast     │
│  construct: overlap / skeleton+broad_nib / skeleton+pointed_pen  │
│  spacing: metrics_keys / tracy / optical                         │
│  checks:  stem_audit / zone_audit / compat / direction           │
└───────────────────────────────▲─────────────────────────────────┘
                                │ 只依赖内核
┌───────────────────────────────┴─────────────────────────────────┐
│  内核（没有任何字母名、没有任何风格枚举）                         │
│  L0 geo      三次曲线、片段、连续性、测量                         │
│  L1 draw     Writer：带命名节点 / 角点槽 / 端点槽的轮廓书写        │
│  L2 glyph    Drawing、Glyph、Project、Master                     │
│  L3 system   System 数值表（对齐区、stems、超调、项目自定义 token）│
│  L4 proof    渲染字串、叠图、测量报告                             │
│  L5 compile  UFO / designspace / fontTools（现有，保留）          │
│  CLI         tk new / tk proof / tk audit / tk build / tk diff   │
└─────────────────────────────────────────────────────────────────┘
```

依赖规则（用 import-linter 之类的工具在 CI 里强制）：

- 内核不 import 插件；插件之间不 import；项目只用公开符号。
- 内核源码里**不得出现字母命名的函数**（`*_from_n`、`build_H`、`n_yoke` 一类）和风格分支（`style.serif == ...`）。
- 插件不得 import 任何 `_` 私有符号。

### 3.2 核心概念

#### `System`：设计师的数值表

```python
# myfont/system.py
from typekernel.system import System, Zones, Overshoot

REGULAR = System(
    upm=1000,
    zones=Zones(base=0, x=520, cap=700, asc=740, desc=-210),
    overshoot=Overshoot(round=12, pointed=10),
    stem={"lc": 84, "lc_h": 70, "uc": 92, "uc_h": 76},
    tokens={"n_width": 430, "o_width": 470, "shoulder_tension": 0.58},
)
```

- 只是数据。所有派生关系（“x 高越大字怀越宽”）要么由设计师写成显式数值，要么写在**项目自己的** `elements.py` 里。
- `tokens` 开放给项目自定义，库不预设语义。
- 预设（`geometric_sans` 等）降级为 starter 模板里的一份 `system.py`。

#### `Fragment`：可复用的路径片段

元素不是闭合实体，而是**开放路径片段**：有起点、终点、两端切线，可以被拼进任何轮廓。

```python
@dataclass(frozen=True)
class Fragment:
    segments: tuple[Segment, ...]       # 三次 / 直线
    nodes: tuple[Node, ...]             # 片段内的命名点（完整契约见 9.2）
    @property
    def start(self) -> Point: ...
    @property
    def end(self) -> Point: ...
    def start_tangent(self) -> Vec: ...
    def end_tangent(self) -> Vec: ...
```

内核提供**不含字母语义的几何构造器**：`tensioned_arc`、`superellipse_quarter`、`spring`（直线进曲线、可带削薄）、`diagonal_band`（带斜笔补偿）、`hook`。“肩”“碗”是用这些拼出来的，放在项目或 starter 里。

#### `Writer`：设计师绕轮廓走一圈

```python
# myfont/glyphs/lower/n.py
from typekernel.draw import Writer, glyph
from myfont.elements import arch            # 项目自己的元素

@glyph("n", group="lc.straight")
def n(s):                                   # s: 当前母版的 System
    st, xh = s.stem["lc"], s.zones.x
    a = arch(s, left=st, counter=s.tokens["n_width"] - 2 * st)

    w = Writer()
    w.start((0, 0)).corner("stem.l.foot.o")
    w.line((0, xh)).corner("stem.l.top.o")
    w.line((st, xh)).node("stem.l.top.i")
    w.fragment(a.outer)                     # 肩外沿；切线由片段保证连续
    w.line((a.outer.end.x, 0)).corner("stem.r.foot.o")
    w.line((a.inner.start.x, 0)).corner("stem.r.foot.i")
    w.fragment(a.inner)                     # 字怀
    w.line((st, 0)).corner("stem.l.foot.i")
    return w.close().build()
```

- 每个点都可以命名（`node`），角点可以声明成**槽**（`corner`），笔画开口可以声明成**端点槽**（`end`）。
- 字形代码只决定**结构和数值**，不知道将来挂什么衬线 / 端点。
- `Writer` 在拼接时检查连续性（声明为平滑的连接必须 G1；可选 G2）。连接不顺就报错，不在事后补。

#### 槽位插件：风格维度和字母解耦

```python
# myfont/font.py
from typekernel.project import Project
from typekernel.plugins.corners import slab, plain
from typekernel.plugins.ends import angled

project = Project(
    system=REGULAR,
    glyphs="glyphs/",
    corners={"*.foot.*": slab(length=0.42, thickness=0.18), "*": plain()},
    ends={"*": angled(deg=12)},
)
```

- 衬线插件只看到一个 `CornerSite`（角点位置、进出边方向、所在 stem 宽、标签），返回替换该角点的片段。
- 无衬线 → 衬线：**改 `font.py` 一行，0 个字形文件改动。**
- 某个字要例外（`r` 只要左脚衬线），在该字形里换标签或声明 `corner(..., fill="plain")`，不改插件。

#### 构造方式也是插件，不是唯一真相

设计师的画法不止一种，三种都应支持：

| 构造方式 | 适用 | 说明 |
| --- | --- | --- |
| `contour`（默认） | 无衬线、几何、工整衬线 | `Writer` 绕外形一圈 + 字怀 |
| `overlap` | 很多设计师的日常做法 | stem、肩各画一块并允许重叠；**接合形状由各块自身形状设计**，静态导出时去除重叠，可变字体保留重叠 |
| `skeleton + pen` | 人文、手写、斜体 | 骨架 + 宽头 / 尖头笔模型生成轮廓（复用现有 `geo.stroke`） |

`overlap` 模式会直接消掉现在 `vf_compat_stem_segments`、“seal crotch”这一大类问题：可变字体里重叠可以保留，母版之间只需要每块形状的点结构一致。

禁令只有一条：**不允许事后修缝。** 连接难看，就去改画这个连接的片段或形状。

#### `Pass`：显式的光学修正

```python
@glyph("b", group="lc.bowl")
def b(s):
    d = draw_b(s)
    d = crotch_thin(d, at="bowl.join.top", amount=0.82)  # 这一刀改了什么，读代码就看得见
    return d
```

光学修正是**写在字形里、可读、可删**的函数调用，不藏在 builder 里。

#### 母版与斜体

- 同一个字形函数用不同母版的 `System` 求值；兼容性靠节点标签 + 段结构检查。
- 某个母版需要不同画法时，用 `@n.master("Black")` 单独覆盖。
- 斜体是 `glyphs_italic/` 下的**另一套字形文件**（可以 import 正体的元素），不是开关。

#### 间距

- `metrics keys`（`n: lsb==stem*0.9`、`h: lsb=n, rsb=n`、`b: lsb=n, rsb=o`），像 Glyphs 一样声明。
- Tracy 法、光学测量做成插件，可选。
- 结果写进 `spacing.py`，agent 可以手调。

### 3.3 测试：按设计师的方式验收

| 层 | 测什么 | 怎么测 | 出现字母名？ |
| --- | --- | --- | --- |
| 内核单测 | 几何契约：片段切线、拼接连续性、标签在变换后保留、测量精度、编译不改点 | 合成形状（矩形、圆环、合成弧） | **不允许** |
| 插件契约测试 | 每个插件对任意合法 `CornerSite` / `EndSite` 产出合法拓扑、方向正确、标签保留、跨母版结构稳定 | 合成角点 / 端点，属性测试 | **不允许** |
| 项目审计 `tk audit` | 设计师会量的东西：stem 实测 vs `System`、对齐区和超调、轮廓方向、母版兼容、侧距与 `n`/`o` 基准的偏差 | 按命名节点测量，输出报告 | 是，在**用户项目**里 |
| 样张 `tk proof` | 设计师会看的东西：控制串、字组串、间距串、字偶串、多字号瀑布、母版叠图、前后对比 | PNG + 视觉 agent / 人工审阅 | 是，在**用户项目**里 |

审计是**诊断**，不是美学上的通过 / 失败门禁（这一点和已经去掉的 hairline 门禁一致）。只有结构性错误（方向、自交、母版不兼容）才算硬失败。

默认样张串（starter 内置，项目可改）：

```
control:  nnonoo  nnhnnhnn  oobobboo  HHOHOO  HOHHOO
lc.n:     nnnmnnnhnnnrnnnunnn
lc.o:     ooobooodoooppooqooo  oocooeoo
diag:     vvwvxvyv  nvnwnxnyn
spacing:  hamburgefonstiv  Hamburgefonstiv  HAMBURGEFONSTIV
kern:     AV Ta To Yo LT P. F,  "ry" "f."
```

---

## 4. agent 的标准工作流（skill 将按此重写）

```
tk new myfont --starter latin-sans      # 拷入 system/elements/控制字模板
1. 写 brief.md
2. 改 system.py（每个数值都要能说出理由）
3. 画控制字 n o H O              → tk proof control   → 看图，改，重复
4. 写 / 改 elements.py（肩、碗、弧）→ 扩字组           → tk proof lc.n / lc.o / diag
5. tk audit                         → 读 stem/zone 偏差，逐字修
6. 选衬线 / 端点插件（font.py）      → tk proof all
7. spacing.py                       → tk proof spacing / kern
8. 母版、斜体                        → tk audit --compat；tk proof ladder
9. tk build                         → OTF / TTF / VF
```

agent 的每一步都在**改自己项目里的代码**，看**自己生成的样张**，和设计师在 Glyphs 里的循环一一对应。

---

## 5. 现有代码的去留

| 现有 | 处理 |
| --- | --- |
| `geo`（contour / segment / path_builder / curves / extrema / joins / stroke / boolean / pens / convert） | **保留为 L0**；`joins.blend_corners` 等降为可选工具，不再是默认路径 |
| `optics` 的测量（stem、whitespace、overshoot） | 保留，改为接收 `Drawing` + `System`，不依赖 `DesignContext` |
| `optics.space` | 拆成 spacing 插件（optical / tracy）+ 内核侧距数据结构 |
| `axes`、`compile` | 保留；去掉对 `parts.DesignContext` 的依赖 |
| `font`（`Font` / `Glyph` / `Component`） | 保留；`Glyph.from_composed` 换成 `from_drawing` |
| `qa.proof` / `specimen_png` / `outline_hash` | 保留并接到 `tk proof`；`outline_hash` 只用于“这次改动是否改了某字”的 diff，不做 golden 门禁 |
| `qa` 的 `score` / `style_consistency` / `originality` / `trial_protocol` / `sentence_gate` / `family_gate` | 冻结，迁移完成后评估删除 |
| `parts.serifs` 的 inline 路径、`terminals`、`aperture` | **提取**成 corners / ends 插件（去掉对字母和 `DesignContext` 的依赖） |
| `parts.control` / `caps` / `diagonals` / `figures` / `punctuation` 的几何 | **不再是库 API**。作为素材，把干净的几何改写进 starter `latin-sans` 的 `elements.py` 和字形文件 |
| `parts.context.DesignContext` / `style.Style` / `glyph_specs` / `family.FormSources` / `skeleton_recipes` / `*_yoke` | 冻结 → 迁移后删除 |
| 引用 `build_n` / `*_from_*` / `*_yoke` / 预设的 80 个测试文件 | 随旧 API 一起移走；有价值的几何契约改写成合成形状测试 |
| `examples/*` | 依赖旧 `parts` 的示例在 M4 出口时删除；新示例全部是 `tk new` 生成的项目 |

**已定决策：旧字母代码不保留冻结副本。** M4 出口时直接删除（git 历史即存档）。M1–M4 期间旧代码只读，可以作为几何参考，不得被新包 import。

---

## 6. 实现路径

每个阶段都有明确出口，没过出口不进下一阶段。旧代码在 M4 之前不删除，只冻结。

### M0 冻结与立规（1–2 天）

- 合入本文；`AGENT_GOAL.md`、skill、README 指向本文。
- 宣布冻结：`parts` 不再新增字母 builder、yoke 参数、风格分支。
- CI 加架构守卫（先对新包生效）：新内核包里禁止字母命名函数、禁止风格枚举分支、禁止跨插件 / 私有导入。

**出口**：守卫在 CI 里能跑；团队（和 agent）不再往 `parts` 加东西。

### M1 内核：Fragment + Writer + Drawing（1–2 周）

- `typekernel.draw`：`Fragment`、`Writer`（`start/line/curve/fragment/node/corner/end/close`）、`Drawing`（多轮廓 + 命名节点 + 槽位清单）。
- 连续性检查：声明平滑的连接必须 G1，误差超限直接报错。
- 内核几何构造器：`tensioned_arc`、`superellipse_quarter`、`spring`、`diagonal_band`、`hook`（从现有 `geo.curves` / `control._shoulder` 中抽出，去掉字母语义）。
- 全部用合成形状测试。

**出口**：用不到 40 行项目代码，画出一个单轮廓 `n`（标签齐全、G1 连续），**不调用任何 `parts` 函数**。

### M2 System + Project + CLI 骨架（1 周）

- `typekernel.system.System`（纯数据）、`typekernel.project.Project`（发现 `glyphs/`、母版、插件配置）。
- `@glyph` 注册、母版求值、`Drawing → font.Glyph → compile` 打通。
- CLI：`tk new`（空模板）、`tk proof <set>`、`tk build`。
- `compile` / `font` / `axes` 去掉对 `DesignContext` 的硬依赖。

**出口**：一个只有 `n o H O` 的项目可以 `tk build` 出 OTF，`tk proof control` 出 PNG。

### M3 槽位插件（1–2 周）

- `plugins.corners`：`plain`、`rounded`、`slab`、`bracketed`、`wedge`、`ink_trap`。
- `plugins.ends`：`flat`、`angled`、`ball`、`flare`。
- `plugins.passes`：`overshoot`、`diagonal_comp`、`crotch_thin`。
- 每个插件 = 一个函数 + 一组契约测试（合成角点 / 端点 × 多 stem 宽 × 多角度）。

**出口（解耦试金石）**：同一份 `n h m H I` 字形文件，只改 `font.py` 的插件配置，就能产出无衬线 / slab / bracketed 三个版本，**字形文件 0 行改动**，样张肉眼合格。

### M4 Starter `latin-sans`：用新方式重做一副字（3–4 周，最关键）

- 按设计师顺序：控制字 `n o H O` → 字组 → 全 ASCII。几何从旧 `parts` 里借，但写成**项目代码**：`elements.py`（arch、bowl、spring、hook…）+ 每字一个文件。
- 每个字组完成后跑 `tk proof <group>`，交视觉审阅；不合格就改片段，**禁止加修缝 pass**。
- `tk audit`：stem、对齐区、兼容、方向审计落地。
- 两个母版（Light / Bold）+ VF，验证 `overlap` 构造下的兼容性。

**出口**：
- 样张水平不低于现在 `skill_validate` 的产出；
- 任意一个字形文件可以独立修改而不影响其他字（除非显式共享元素）；
- 全项目不 import `typekernel.parts`。

达到后：删除旧 `parts` 字母代码、`DesignContext` / `Style` / `glyph_specs` / `FormSources`，以及依赖它们的测试和示例（不保留冻结副本）。

### M5 设计师式验收 + skill 重写（1–2 周）

- 内置样张串、母版叠图、改动前后 diff、多字号瀑布。
- 重写 `.agents/skills/typekernel-font-design/`：教第 4 节的工作流，教如何读样张和审计报告，教“改片段而不是加补丁”。
- 用一个**全新 agent 会话**做试字：只给 brief 和 skill，看它能不能做出一副风格不同的字（例如窄体 slab）。

**出口**：新会话的 agent 不读库源码，只读 skill + starter，就能完成控制字 → 字组 → 构建，并且做出的形状和 starter 有明显区别（证明它在设计，而不是在调参）。

### M6 扩展构造方式与第二个 starter（之后）

- `skeleton + pen` 构造插件（复用 `geo.stroke`），做 `latin-humanist-italic` starter。
- 第二个 starter 证明：内核和插件**零修改**就能承载不同的字体类型。
- 再往后：非拉丁文字（只需新 starter 和新插件，内核不改）。

**已落地（控制字切片）**：`plugins.construct.skeleton_pen`（`broad_nib` / `pointed_pen` / `expand_skeleton` / `expand_skeleton_cubic`）+ starter `latin_humanist_italic`（`n o H O`）+ `tk new --starter latin-humanist-italic`。内核不改；字组扩展、spacing、斜体母版仍属后续。

---

## 7. 守住方向的检查清单

每个 PR 都问这几条；任何一条答“是”，说明在往回走：

1. 内核或插件里出现了字母名函数、或对某个风格值的 `if` 分支？
2. 为了让某个字好看，加了一个事后修缝 / 封口 / 软化的处理，而不是改画这个连接的片段？
3. 一个字的几何由另一个字的函数**隐式**推出（`x_from_y(...)` 里藏着几百行）？
4. 新加的参数只对库自带的那副字有意义？
5. 库测试里出现了具体字母，或者锁定了某副字的轮廓哈希 / 段数？
6. agent 想改一个细节，只能去改库，而不能改自己项目里的文件？

衡量进展的指标：

| 指标 | 现在 | M4 后目标 |
| --- | --- | --- |
| 内核里字母命名的公开函数（`*_from_*` / `build_*` / `*_yoke`） | 约 190 | 0 |
| 风格分支（serif / italic / vf_compat） | 约 250 处 | 0（变成插件和独立字形文件） |
| 切换衬线风格需要改的文件 | 7 个库模块 | 项目里 1 行配置 |
| 库测试里引用具体字母的文件 | 80 | 0（只剩合成形状） |
| 事后修缝函数调用 | 107 处 | 0（默认路径） |

---

## 8. 有意不做

- 不做 GUI 编辑器；agent 的“编辑器”就是字形文件 + 样张。
- 不在内核里放“能自动生成全套字”的工厂（包括“方便起见”的 `build_all`）。
- 不用数值门禁冒充美学判断；美学由视觉审阅决定。
- 不为了兼容旧 API 长期维持双轨：M4 出口后旧路径直接删除。

---

## 9. 交接规格（给实现者）

本节是可以直接照着写代码的契约。签名是规范性的；内部实现自由。和第 3 节冲突时以本节为准。

### 9.1 新包布局

```
src/typekernel/
  geo/                 # 现有，保留；只补纯几何工具
  draw/
    __init__.py        # 公开：Fragment, Writer, Drawing, ContourRole, Node, Slot
    fragment.py        # Fragment + 变换
    writer.py          # Writer
    drawing.py         # Drawing、标签查询、槽位清单、兼容签名
    construct.py       # 不含字母语义的几何构造器
    slots.py           # CornerSite / EndSite / 填充协议 / 槽位应用
  system/
    __init__.py        # 公开：System, Zones, Overshoot
  project/
    __init__.py        # 公开：Project, glyph, Master
    registry.py        # @glyph 发现与注册
    evaluate.py        # 按母版求值 → Drawing → font.Glyph
  plugins/
    corners/  ends/  passes/  spacing/  checks/  construct/
  cli/
    __main__.py        # tk new / proof / audit / build / diff
  starters/
    latin_sans/              # tk new --starter latin-sans
    latin_humanist_italic/   # tk new --starter latin-humanist-italic（M6 控制字）
```

`draw` / `system` / `project` / `cli` 是内核；`plugins` 是插件；`starters` 是模板数据，**不被任何内核模块 import**。

### 9.2 `draw.Fragment`

```python
Segment = LineSegment | CubicSegment          # 复用 geo.segment

@dataclass(frozen=True, slots=True)
class Node:
    index: int                # 在片段 / 轮廓中的 on-curve 序号（0 = 起点）
    tag: str                  # 点分命名，如 "stem.l.foot.o"
    meta: Mapping[str, float] # 可选：stem 宽等给插件读的提示

@dataclass(frozen=True, slots=True)
class Fragment:
    segments: tuple[Segment, ...]             # 首尾相接，非空
    nodes: tuple[Node, ...] = ()              # 片段内的命名点（可选）

    start: Point;  end: Point                 # property
    def start_tangent(self) -> Point: ...     # 单位向量
    def end_tangent(self) -> Point: ...
    def reversed(self) -> Fragment: ...       # 方向反转，节点 index 重映射
    def translated(self, dx: float, dy: float = 0.0) -> Fragment: ...
    def mirrored_x(self, axis_x: float) -> Fragment: ...   # 镜像并反转方向，保持绕向语义
    def mirrored_y(self, axis_y: float) -> Fragment: ...
    def tagged(self, prefix: str) -> Fragment: ...         # 给所有节点 tag 加前缀
```

规则：

- 构造时校验首尾相接（精确相等或 `1e-9` 内），否则 `ValueError`。
- 片段内部相邻段之间，若任一侧是曲线，必须 G1（复用 `geo.smoothness.g1_join_error`，容差 `1e-6`），除非该节点 `meta` 含 `cusp=1`。
- 不引入任何坐标采样；所有变换都作用在控制点上。

### 9.3 `draw.Writer`

```python
class Writer:
    def start(self, p: PointLike) -> Writer
    def line(self, p: PointLike) -> Writer
    def curve(self, c1: PointLike, c2: PointLike, p: PointLike) -> Writer
    def fragment(self, f: Fragment, *, prefix: str = "") -> Writer
        # f.start 必须等于当前点；否则 ValueError（不自动连线）
    def node(self, tag: str, **meta: float) -> Writer       # 给“当前点”命名
    def corner(self, tag: str, **meta: float) -> Writer     # 当前点 = 角点槽（允许不连续）
    def cusp(self) -> Writer                                 # 当前点允许切线不连续，但不是槽
    def end(self, tag: str, **meta: float) -> Writer        # 下一段 = 端点槽（笔画切口）
    def close(self, role: ContourRole = "ink") -> Writer    # 闭合当前轮廓，可继续 start 下一个
    def build(self) -> Drawing
```

语义：

1. **连续性在书写时检查，不在事后修。** `close()` 和 `build()` 时检查每个 on-curve 节点：若相邻两段至少一段是曲线，则必须 G1；被 `corner()` / `cusp()` 标记的节点除外。失败抛 `ContinuityError`，信息里带节点 tag 或坐标、实测角度。
2. **两段都是直线的节点**默认允许转角，不需要声明。
3. `role="ink"` 的轮廓在 `build()` 时规范为逆时针，`"counter"` 规范为顺时针（与现有 `_ccw` 约定一致，方向反转时节点 index 同步重映射）。
4. 同一 `Drawing` 内 tag 必须唯一；重复抛 `ValueError`。
5. `Writer` 不知道任何字母、风格或 `System`。

### 9.4 `draw.Drawing`

```python
ContourRole = Literal["ink", "counter"]

@dataclass(frozen=True, slots=True)
class Slot:
    kind: Literal["corner", "end"]
    tag: str
    contour: int
    node: int                 # corner：角点 index；end：切口段起点 index
    meta: Mapping[str, float]
    fill: str | None = None   # 字形内显式指定的填充名，覆盖项目配置

@dataclass(frozen=True, slots=True)
class Drawing:
    contours: tuple[Contour, ...]
    roles: tuple[ContourRole, ...]
    nodes: tuple[tuple[Node, ...], ...]       # 每个轮廓的命名点
    slots: tuple[Slot, ...]

    def point(self, tag: str) -> Point
    def find(self, pattern: str) -> list[Node]          # fnmatch 风格匹配点分 tag
    def outline(self) -> Outline                        # 交给 compile / optics
    def signature(self) -> tuple                         # 兼容签名：每轮廓 (role, 段类型序列, tag 序列)
    def __add__(self, other: Drawing) -> Drawing         # 叠加（overlap 构造）；tag 冲突报错
    def translated(...); def mirrored_x(...)             # 同 Fragment
```

两个母版的 `signature()` 相等，就说明它们**结构可插值**（M1 只做签名，插值检查在 M2 接 `axes.interpolatable`）。

### 9.5 槽位与填充协议（`draw.slots`，M1 定义，M3 实现插件）

```python
@dataclass(frozen=True, slots=True)
class CornerSite:
    tag: str
    point: Point
    in_dir: Point             # 进入角点的单位方向
    out_dir: Point            # 离开角点的单位方向
    in_len: float             # 进入边可裁剪的最大长度
    out_len: float
    role: ContourRole
    meta: Mapping[str, float]

@dataclass(frozen=True, slots=True)
class CornerFill:
    trim_in: float            # 从角点沿进入边回退的距离
    trim_out: float           # 沿离开边前进的距离
    path: Fragment | None = None  # 替换路径；None + 零 trim = 几何 no-op（≡ plain / 未匹配）

class CornerFiller(Protocol):
    def __call__(self, site: CornerSite, system: System) -> CornerFill: ...

@dataclass(frozen=True, slots=True)
class EndSite:
    tag: str
    a: Point; b: Point        # 切口段两端（按轮廓方向）
    a_dir: Point              # 到达 a 的笔画边方向
    b_dir: Point              # 离开 b 的笔画边方向
    role: ContourRole
    meta: Mapping[str, float]

@dataclass(frozen=True, slots=True)
class EndFill:
    trim_a: float; trim_b: float
    path: Fragment | None = None  # None + 零 trim = 几何 no-op（≡ 未匹配；退化参数同）

class EndFiller(Protocol):
    def __call__(self, site: EndSite, system: System) -> EndFill: ...

def apply_slots(
    d: Drawing,
    system: System,
    corners: Mapping[str, CornerFiller],   # 键是 tag 模式，按插入顺序首个匹配生效
    ends: Mapping[str, EndFiller],
    named: Mapping[str, CornerFiller | EndFiller] = {},  # 供 Slot.fill 显式引用
) -> Drawing
```

规则：

- 未匹配任何模式的槽保持原样（等价于 `plain`）。显式 `plain()` 与退化参数（如 `rounded(radius=0)`、`ball(radius=0)`、`flare(amount=0, depth=0)`、`angled(deg=0)`、`flat(inset=0)`）必须走同一 no-op：`trim=0` 且 `path=None`，不插入零长段、不消费角点/端点槽。
- 填充后的轮廓仍要通过 9.3 的连续性检查；插件产生不连续视为插件 bug。零长段不得靠 post-fill「跳过」蒙混——故意保留的切线不连续只走角点槽豁免；line–line 接合不要求 G1。
- 填充是**确定性**的：同一 `System` 结构下，不同母版填充出的段类型序列必须相同（插件契约测试覆盖）。
- `trim_in > in_len` 或路径首尾不落在裁剪点上 → `SlotFillError`。

### 9.5b 构造插件 `plugins.construct`（M6）

字母无关。项目提供骨架，插件只负责笔模型展开为 `Drawing`：

```python
def broad_nib(thickness: float, *, contrast: float = 0.55, angle_deg: float = 30.0) -> Pen
def pointed_pen(thickness: float, *, contrast: float = 1.0, angle_deg: float = 0.0) -> Pen
def expand_skeleton(centerline, pen, *, join="round", cap="round", miter_limit=4.0) -> Drawing
def expand_skeleton_cubic(centerline, pen, *, join="round", cap="round", ...) -> tuple[Drawing, CenterlineExpandReport]
```

规则：

- 复用 `geo.stroke.Pen` / `Centerline` / `CubicCenterline` / `expand` / `expand_cubic`；不 import starter，不出现字母名。
- 展开结果去掉近零长线段；单轮廓一律 `ink`（必要时翻成 CCW）；环：最大 |area| → `ink`，其余 → `counter`。
- 无角点/端点槽的 skeleton 字形：`Project` 可不配置 `corners`/`ends`，从而跳过 `apply_slots`（笔迹接合不是 Writer G1 链）。
- `blend_corners` / heal / seal **不是**本插件路径。

### 9.6 几何构造器（`draw.construct`，M1）

全部只接收几何量，不接收 `System`，不出现字母名：

```python
def tensioned_arc(p0, t0, p1, t1, *, tension: float = 0.55) -> Fragment
    # 从 p0 沿 t0 出发、沿 t1 到达 p1 的单段三次；tension 为手柄长 / 弦长比例
def superellipse_quarter(center, rx, ry, quadrant: int, *, exponent: float) -> Fragment
    # 复用 geo.curves.superellipse_kappa
def spring(stem_edge_x: float, y_from: float, y_to: float, toward: Point,
           *, depth: float, tension: float) -> Fragment
    # 直线笔画边进入曲线的过渡段（肩 / 碗接干处），保证 G1
def diagonal_band(p_top: Point, p_bottom: Point, *, weight: float, compensate: bool = True) -> tuple[Fragment, Fragment]
    # 斜笔两条边，weight 为期望的视觉粗细，compensate 时按角度修正垂直宽
def hook(
    stem_edge_x: float,
    y_join: float,
    tip: Point,
    *,
    depth: float,
    tension: float = 0.55,
    tip_tangent: Point | None = None,
) -> Fragment
    # 竖直干边 (stem_edge_x, y_join) 出发的钩形终端：G1 离开干（竖直切线朝 tip.y），
    # 经 depth 控制的腹点到 tip；默认 tip 切线水平回指干（回卷）。两段 tensioned_arc，腹点 G1。
```

可以从 `geo.curves`、`geo.path_helpers` 以及旧 `parts.control._shoulder` 的数学中**抄思路**，但不得 import `typekernel.parts`。

### 9.7 `System`（M2）

```python
@dataclass(frozen=True, slots=True)
class Zones:   base: float = 0; x: float; cap: float; asc: float; desc: float
@dataclass(frozen=True, slots=True)
class Overshoot:  round: float; pointed: float

@dataclass(frozen=True, slots=True)
class System:
    upm: float
    zones: Zones
    overshoot: Overshoot
    stem: Mapping[str, float]           # 自由键，如 "lc" / "lc_h" / "uc"
    tokens: Mapping[str, float] = {}    # 项目自定义
    def tuned(self, **kw) -> System
```

不得有 `aperture` / `roundness` 这类“一个数影响多处几何”的旋钮。

### 9.7a `Project` / `@glyph` / `Master`（M2）

```python
@dataclass(frozen=True, slots=True)
class Master:
    name: str
    system: System

def glyph(name: str, *, group: str = "") -> Callable[[GlyphFn], GlyphFn]:
    """Register a glyph builder. ``fn(system) -> Drawing``.

    Attach master overrides with ``@fn.master("Black")`` on a second function
    of the same shape. Glyph ``name`` is a production name (may be a letter in
    *projects*); kernel tests must still use synthetic names (§9.8 rule 5).
    """

@dataclass(frozen=True, slots=True)
class GlyphSpec:
    name: str
    group: str
    build: Callable[[System], Drawing]
    masters: Mapping[str, Callable[[System], Drawing]]  # override builders

class Project:
    def __init__(
        self,
        system: System,
        glyphs: str | Path,
        *,
        masters: Sequence[Master] = (),
        corners: Mapping[str, CornerFiller] | None = None,
        ends: Mapping[str, EndFiller] | None = None,
        default_advance: float | None = None,
    ) -> None: ...
    def discover(self) -> None:
        """Import every ``*.py`` under ``glyphs`` and collect ``@glyph`` specs."""
    def specs(self) -> Mapping[str, GlyphSpec]: ...
    def evaluate(self, name: str, *, master: str | None = None) -> Drawing:
        """Run the glyph (or its master override) with the resolved System.
        Applies ``corners`` / ``ends`` via ``apply_slots`` when configured.
        """
    def to_glyph(self, name: str, *, master: str | None = None, advance: float | None = None) -> "font.Glyph":
        """``evaluate`` then wrap contours as ``font.Glyph`` (advance default:
        bbox width, or ``default_advance``, or ``tokens['advance']``)."""
```

规则：

- `@glyph` 注册发生在模块 import 时；`discover()` 负责把 `glyphs/` 加进导入路径并加载。
- 默认母版用 `Project.system`；`masters` 里同名覆盖 `System`，字形侧 `@build.master(name)` 覆盖画法。
- `Project` / `glyph` / `Master` / `GlyphSpec` 是内核公开符号；不 import `parts`。

### 9.8 架构守卫（M0，CI 必跑）

`tests/architecture/test_boundaries.py`，对 `draw` / `system` / `project` / `cli` / `plugins` 生效：

1. 禁止 import `typekernel.parts`（M4 后对全仓生效）。
2. 函数名不得匹配 `^(build_[A-Za-z]|[A-Za-z]_|[a-z]+_from_[A-Za-z]|\w+_yoke)$`。
3. 源码不得出现 `style.serif`、`italic_slant_deg`、`vf_compat`。
4. `plugins/<x>/` 不得 import `plugins/<y>/`；任何新包不得 import 其他模块的 `_` 私有名。
5. 内核测试（`tests/draw`、`tests/system`、`tests/project`）里不得出现字母字形名字符串（用一个小正则：单字母 glyph 名或 `uniXXXX`）；需要形状时用合成夹具。

用 `ast` 扫描实现，不额外引入依赖。

### 9.9 M1 测试清单（全部合成形状）

| 测试 | 断言 |
| --- | --- |
| Fragment 首尾不接 | `ValueError` |
| Fragment 内曲线接合不 G1 且无 cusp | `ContinuityError` |
| `reversed` / `mirrored_x` | 段几何正确、节点 index 正确重映射、tag 保留 |
| Writer 画矩形 | 4 直线、无需声明角点、逆时针 |
| Writer 画“直线进曲线”且不 G1 | `ContinuityError`，信息含坐标 |
| 同上但标 `corner()` | 通过，生成一个 corner 槽 |
| `fragment()` 起点不等于当前点 | `ValueError` |
| `role="counter"` | 顺时针；节点 index 随反转重映射 |
| tag 重复 | `ValueError` |
| `signature()` | 参数不同（宽度 / stem）但同一书写程序 → 签名相等；多一段 → 不等 |
| `Drawing + Drawing` | 轮廓叠加、tag 冲突报错 |
| `apply_slots` 用测试内的假填充 | 角点被替换、仍连续、未匹配槽不变、`trim` 越界报错 |
| `tensioned_arc` / `superellipse_quarter` / `spring` | 端点、端切线正确；与相邻直线 G1 |
| `hook` | 干接合 G1；终点 = tip；腹点在干同侧且 |Δx|≈depth；默认 tip 切线回指干 |
| `diagonal_band(compensate=True)` | 垂直于笔画方向的实测宽度 = `weight`（容差 0.5 单位） |
| M1 出口样例 | 一个“直干 + 拱 + 直干”的合成单轮廓（测试里叫 `arch_body`，不叫 `n`），≤ 40 行，全部节点 G1 或已声明角点 |

### 9.10 里程碑任务拆分（每条一个提交）

**M0**
1. `docs`：本文入口 —— README、`VISION.md`、`AGENT_GOAL.md` 顶部指向本文；`AGENT_GOAL.md` 中 yoke 教学标注“迁移中，见 ARCHITECTURE.md”。
2. `docs(skill)`：skill 顶部加冻结声明（不再新增 builder / yoke 参数 / 风格分支；新工作走 `draw`）。
3. `test(architecture)`：9.8 守卫（新包为空时也能跑通）。

**M1**
4. `feat(draw)`：`Fragment` + `Node` + 变换 + 测试。
5. `feat(draw)`：`Writer` + `Drawing` + 连续性检查 + 方向规范 + 测试。
6. `feat(draw)`：`signature()` 与叠加。
7. `feat(draw)`：槽位数据结构、`apply_slots`、填充协议 + 假填充测试。
8. `feat(draw)`：`construct` 构造器 + 测试。
9. `test(draw)`：M1 出口样例 `arch_body`。

**M2**
10. `feat(system)`：`System` / `Zones` / `Overshoot`。
11. `feat(project)`：`@glyph` 注册、目录发现、母版求值。
12. `refactor(font,compile,axes)`：接受 `Drawing` / `System`；去掉对 `parts.DesignContext` 的硬依赖（保留旧入口到 M4）。
13. `feat(cli)`：`tk new`（空模板）、`tk build`、`tk proof <set>`（复用 `qa.proof`）。
14. `test(project)`：一个只含合成字形的临时项目端到端出 OTF。

**M3**（每个插件一个提交：实现 + 契约测试）
15–20. `corners.plain/rounded/slab/bracketed/wedge/ink_trap`
21–24. `ends.flat/angled/ball/flare`
25–27. `passes.overshoot/diagonal_comp/crotch_thin`
28. `test(plugins)`：解耦试金石——同一组合成字形 × 三种 corner 配置，字形源码哈希不变。

**M4**（每个字组一个提交，每个提交附样张，视觉审阅不过不进下一组）
29. `starters/latin_sans`：`system.py` + `elements.py` + `n o H O`
30. 小写 n 组 → o 组 → 斜笔组 → 其余小写
31. 大写 H 组 → O 组 → 斜笔组 → 其余
32. 数字、标点
33. `spacing.py`（metrics keys）+ 字偶
34. Light / Bold 母版 + VF（overlap 构造）
35. `tk audit`：stem / zone / compat / direction
36. **删除**：`parts` 字母代码、`DesignContext`、`Style`、`glyph_specs`、`FormSources`、`skeleton_recipes`、相关测试与示例、golden outline hash；守卫第 1 条扩到全仓

**M5**
37. 重写 `.agents/skills/typekernel-font-design/`（按第 4 节工作流）
38. 新会话试字记录写进 `docs/AGENT_TRIALS.md`

### 9.11 给实现模型的硬约束

- 不要“顺手”修旧 `parts`；M4 前它只读。
- 遇到某个连接画不好，**改构造器或片段**，不加任何事后的 blend / seal / heal pass。
- 新增公开符号必须出现在本文 9.2–9.7 或先补进本文。
- 不要为了让测试通过而放宽连续性容差；容差变更要写进本文。
- 提交信息遵循 conventional commits，不用内部编号。
