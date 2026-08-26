# KIMI UI DECISION — Rizum UV Compare 面板重设计

> 配套原型：`prototype/kimi_uv_compare_ui_prototype.html`（THROWAWAY PROTOTYPE，离线单文件）。
> 用 `?variant=A|B|C`、底部浮动切换器或 ← / → 键切换三个方案。
> 本文档是唯一设计依据；实现者按第 6 节的映射逐项复刻，不再做设计判断。

---

## 1. 最终推荐：Variant B（Action-first）

**面板自上而下：Compare 按钮 → 结果区 → Sync 状态行 → 折叠的 Advanced 子面板（容差 + 技术数值）。**

为什么是 B：

- 高频工作流是“换一对岛 → 再按一次 Compare”（后端能力 9）。按钮固定在面板顶部、结果紧随其后，鼠标与视线的移动距离最短，每次操作落点不变。
- 容差是“设一次就忘”的参数（默认 1e-5 覆盖绝大多数情况），不值得占据主界面首屏 → 移入 `DEFAULT_CLOSED` 子面板。
- `max UV difference` 这类技术数值（用户明确不想在主界面看到）降级到 Advanced 子面板与状态栏 report，主结果区只留人话结论。
- 被否方案：
  - **A（Settings-first，现结构的精修版）**：把很少改动的 Tolerance 和只读的 Sync 状态放在按钮之前，首屏被低频信息占据，每次重复操作都要越过它们。
  - **C（Result-first）**：结果横幅置顶强化了“检查工具”语义，但把主动作压到第二屏位；且 NONE 状态下横幅是空壳，浪费最宝贵的顶部空间。适合报表，不适合反复点的工具。

---

## 2. 后端能力 → 界面去向

| # | 后端能力 | 去向 |
|---|---------|------|
| 1 | 比较两个完整选中的 UV 岛 | 主界面：Compare 按钮 |
| 2 | UV Sync 开/关两种选择来源 | 主界面：只读状态行（按钮下方小字，LINKED/UNLINKED 图标）。**不做成开关**——该开关在 UV 编辑器头部已有，重复提供会产生“结果到底按哪种选择算的”的疑惑 |
| 3 | 8 种方向关系识别 | 主界面：MATCH 时显示短关系名（映射表见第 3 节） |
| 4 | 忽略平移/不忽略缩放形变拓扑 | 不进界面（README/文档层面的事） |
| 5 | tolerance 1e-8…1e-2，默认 1e-5 | 仅 Advanced 子面板（折叠） |
| 6 | NONE/MATCH/NO_MATCH/ERROR 四态 | 主界面：结果区四态渲染（第 4 节） |
| 7 | 错误详情（无 UV Map、岛数量≠2 含具体数量） | 主界面：仅错误时显示，alert 红字；面数/loop 数不同属 NO_MATCH，原因作为结果区第二行 |
| 8 | max UV difference | **不在主界面**。仅 Advanced 子面板一行 + operator `self.report()` 状态栏消息（现状已有，保留） |
| 9 | 高频重复比较 | 结果在下次点击 Compare 前保持不变；NONE 态提示文案常驻结果区 |
| 10 | 只读检查、不改 UV | 无需界面表达 |

---

## 3. 精确文案（全部，含字符数预算）

面板宽约 300–360px，单行安全上限按 **≤40 字符** 控制；下表所有字符串均已满足。

### 3.1 固定文案

| 位置 | 文案 | 说明 |
|------|------|------|
| 按钮 | `Compare Selected Islands`（icon `VIEWZOOM`） | 沿用现名 |
| NONE 第一行 | `No comparison yet.`（icon `QUESTION`） | |
| NONE 第二行（灰） | `Select two complete UV islands.` | 合并了原来的常驻提示 label |
| NO_MATCH 第一行 | `No match`（icon `X`） | |
| ERROR 第一行（红） | `Cannot compare`（icon `ERROR`） | |
| Advanced 子面板标题 | `Advanced` | |
| Tolerance 属性 | `Tolerance` | 现有 prop，原样移入 |
| Sync 行（开） | `UV Sync on — mesh selection`（icon `LINKED`） | |
| Sync 行（关） | `UV Sync off — UV selection`（icon `UNLINKED`） | |

### 3.2 MATCH 第一行：`Match — <短关系名>`

后端 `TRANSFORMS` label → 界面短名（最长 34 字符）：

| 后端 label | 界面文案 |
|-----------|---------|
| Same orientation | `Match — Same orientation` |
| Mirrored horizontally (X) | `Match — Mirrored horizontally` |
| Mirrored vertically (Y) | `Match — Mirrored vertically` |
| Rotated 180° | `Match — Rotated 180°` |
| Rotated 90° counter-clockwise | `Match — Rotated 90° CCW` |
| Rotated 90° clockwise | `Match — Rotated 90° CW` |
| Mirrored across X=Y | `Match — Mirrored diagonally (X=Y)` |
| Mirrored across X=-Y | `Match — Mirrored diagonally (X=-Y)` |

### 3.3 结果区第二行（仅 NO_MATCH / ERROR）

| 情形 | 文案 |
|------|------|
| NO_MATCH · 形状/形变差异 | `Islands differ beyond tolerance.` |
| NO_MATCH · 面数不同 | `Different face counts (12 vs 10).`（数字动态） |
| NO_MATCH · loop 数不同 | `Different UV loop counts (48 vs 40).`（数字动态） |
| ERROR · 无 UV Map | `The active mesh has no UV map.` |
| ERROR · 岛数量≠2 | `Found 3 islands, need exactly 2.`（数字动态，0/1/3+ 同句式） |

### 3.4 Advanced 子面板内（仅已比较过时显示）

| 情形 | 文案 |
|------|------|
| MATCH | `Max UV difference: 1.1e-07`（值动态，`:.3g` 格式） |
| NO_MATCH（形状） | `No transform matched within tolerance 1e-05.`（值动态，`%g`） |
| NO_MATCH（面数） | `Different face counts: 12 vs 10.`（即后端原句） |
| ERROR | 后端原始完整信息原样一行（如 `Select exactly two complete UV islands (found 3).`） |

---

## 4. 状态渲染规则

| 状态 | 第一行 | 第二行 | alert |
|------|--------|--------|-------|
| NONE | `QUESTION` + `No comparison yet.` | 灰色提示 `Select two complete UV islands.` | 否 |
| MATCH | `CHECKMARK` + `Match — <关系>` | 无 | 否 |
| NO_MATCH | `X` + `No match` | 原因（普通色，缩进对齐） | 否 |
| ERROR | `ERROR` + `Cannot compare` | 原因（普通色，缩进对齐） | **仅第一行** `alert=True` |

- MATCH **不做绿色**：Blender Python 无法控制 label 颜色，唯一颜色杠杆是 `row.alert`（主题红）。绿色不可行也不必要，`CHECKMARK` 图标已足够。
- NO_MATCH 不用红：它是合法结论而非用户错误；红只留给 ERROR。
- 结果持久：任何选择/状态变化不清空结果区，只有再次执行 operator 才更新（与后端现状一致）。
- operator `poll` 失败（非编辑态网格）时按钮由 Blender 自动置灰，无需额外处理。

---

## 5. 对当前界面（截图）的删除/合并清单

| 现有元素 | 处置 |
|---------|------|
| 常驻 `Select two complete UV islands.` label | **删除**，并入结果区 NONE 态第二行 |
| `UV Sync: using …` 独立 box | **删除 box**，降级为结果区下方一行小字（不换文案含义，文案改为 `UV Sync on/off — …` 短式） |
| 主界面 Tolerance box | **移入** Advanced 子面板（`DEFAULT_CLOSED`） |
| `Last Result` 结果 box 标题行 | **删除**，状态图标直接放在结论文案行 |
| `textwrap.wrap(message, 38)` 整段消息 | **删除**——它正是 “`(ma…` / `difference 1.13e-07).`” 断行丑态的根源；改为结构化的“结论行 + 可选原因行”，不再显示完整后端句子 |
| `(max UV difference 1.13e-07)` | **从主界面移除**，见 2.8/3.4 |

存储相应调整：`rizum_uv_compare_last_result` 单字符串拆为三个 WM 属性（见 6.0），operator 的 `self.report()` 仍用原完整技术句子。

---

## 6. HTML 视觉结构 → Blender Python layout API 映射（Variant B 逐项）

### 6.0 存储（WindowManager 属性）

| HTML 数据源 | Blender |
|-------------|---------|
| `state.last.status` | `wm.rizum_uv_compare_last_status`（Enum，现有，保留） |
| `state.last.headline` | `wm.rizum_uv_compare_last_headline`（新增 `StringProperty`，`options={'HIDDEN'}`，默认 `""`） |
| `state.last.detail` | `wm.rizum_uv_compare_last_detail`（新增，同上） |
| `state.last.technical` | `wm.rizum_uv_compare_last_technical`（新增，同上；存 3.4 的技术行，无则 `""`） |
| `state.tolerance` | `wm.rizum_uv_compare_tolerance`（现有 FloatProperty，不动） |

`store_result()` 改为写以上四项；`compare_islands`/`compare_selected_islands` 返回值相应扩展（比较算法不动，只多带出关系短名/计数/diff）。

### 6.1 主面板 `UV_PT_rizum_compare.draw()` 自上而下

| # | HTML 元素 | Blender 调用 |
|---|-----------|--------------|
| 1 | 大 Compare 按钮（`.op.big`，30px 高） | `col = layout.column(); col.scale_y = 1.3; col.operator("uv.rizum_compare_islands", text="Compare Selected Islands", icon='VIEWZOOM')` |
| 2 | 结果 `.box` | `box = layout.box()`，内部按状态分支： |
| 2a | NONE 两行 | `box.label(text="No comparison yet.", icon='QUESTION')`；`box.label(text="Select two complete UV islands.")`（“灰色”不可控，接受主题默认色） |
| 2b | MATCH 一行 | `box.label(text=wm.rizum_uv_compare_last_headline, icon='CHECKMARK')` |
| 2c | NO_MATCH 两行 | `box.label(text="No match", icon='X')`；若 detail 非空：`box.label(text=wm.rizum_uv_compare_last_detail)`（原生无法缩进第二行，直接齐行即可） |
| 2d | ERROR 两行 | `row = box.row(); row.alert = True; row.label(text="Cannot compare", icon='ERROR')`；detail 非空则 `box.label(text=detail)`（**不加** alert） |
| 3 | Sync 状态行 `.sync-line` | 开：`layout.label(text="UV Sync on — mesh selection", icon='LINKED')`；关：`layout.label(text="UV Sync off — UV selection", icon='UNLINKED')`。读取 `context.scene.tool_settings.use_uv_select_sync`，只读，不包 box |
| 4 | Advanced 子面板 | 新建 `UV_PT_rizum_compare_advanced(bpy.types.Panel)`：`bl_parent_id = "UV_PT_rizum_compare"`，`bl_label = "Advanced"`，`bl_options = {'DEFAULT_CLOSED'}`，space/region/category/poll 与主面板相同。Blender 自绘三角与开合状态，不用自定义 disclosure |
| 4a | Tolerance 行 | 子面板内：`layout.prop(wm, "rizum_uv_compare_tolerance", text="Tolerance")` |
| 4b | 技术行 | 子面板内：`tech = wm.rizum_uv_compare_last_technical`；`if tech: layout.label(text=tech)` |
| — | HTML 里的 `RECOMMENDED` 角标、切换器、评审控件、SVG 画布 | 均不进入插件 |

### 6.2 其余变体（未采用，仅说明结构差异）

- **A**：主面板 draw 顺序为 `layout.label(icon='UV')` 提示 → sync box → tolerance prop → `scale_y=1.3` 按钮 → 结果 box；无子面板。若实现，全部用上表同款调用，仅顺序不同。
- **C**：结果 box 置顶 → 普通高度按钮（不设 `scale_y`）→ `bl_parent_id` 子面板改名 `Details`，内容 = sync 行 + tolerance + 技术行。

### 6.3 明确不做的事

- 不自定义颜色/字体/圆角/阴影/hover 动画；不用 GPU canvas、自定义绘制或图标资源。
- 不给结果区加绿/黄配色；不试图让 label 自动换行（所有文案已按 ≤40 字符预裁）。
- 不把 Sync 做成 prop 开关；不在主界面显示任何科学计数法数值。
