# KIMI UI DECISION — Rizum UV Compare 面板重设计

> 配套原型：`prototype/kimi_uv_compare_ui_prototype.html`（THROWAWAY PROTOTYPE，离线单文件）。
> 用 `?variant=A|B|C`、底部浮动切换器或 ← / → 键切换三个方案。
> 本文档是唯一设计依据；实现者按第 6 节的映射逐项复刻，不再做设计判断。

---

## 1. 最终推荐：Variant B（Action-first）

**面板自上而下：Compare 按钮 → 初始提示/实际结果 → 折叠的 Advanced 子面板（仅容差）。**

> 用户查看原型后的最终裁决：删除插件内的 Sync 状态行。插件在 Sync 开/关时均可工作，当前状态已经由 Blender UV Editor 顶栏表达，面板不重复显示。
>
> 第二次裁决（K3 high）：初始时不画空结果 box，只显示一行 `INFO · Results will appear here`；首次比较后原位替换为真实结果 box。`Max UV difference` 从所有插件界面和状态栏 report 中完全移除。
>
> 第三次裁决（K3 high）：不使用 `self.report`。每次比较后，持久结果框在原位显示 `FILE_REFRESH · Updated` 1.2 秒，再恢复实际结果。连续点击只刷新最新时间戳；旧 timer 不得提前恢复。

为什么是 B：

- 高频工作流是“换一对岛 → 再按一次 Compare”（后端能力 9）。按钮固定在面板顶部、结果紧随其后，鼠标与视线的移动距离最短，每次操作落点不变。
- 容差是“设一次就忘”的参数（默认 1e-5 覆盖绝大多数情况），不值得占据主界面首屏 → 移入 `DEFAULT_CLOSED` 子面板。
- `max UV difference` 这类技术数值对当前工作流没有决策价值，完全不显示；主结果区只留人话结论。
- 被否方案：
  - **A（Settings-first，现结构的精修版）**：把很少改动的 Tolerance 和常驻提示放在按钮之前，首屏被低频信息占据，每次重复操作都要越过它们。
  - **C（Result-first）**：结果横幅置顶强化了“检查工具”语义，但把主动作压到第二屏位；且 NONE 状态下横幅是空壳，浪费最宝贵的顶部空间。适合报表，不适合反复点的工具。

---

## 2. 后端能力 → 界面去向

| # | 后端能力 | 去向 |
|---|---------|------|
| 1 | 比较两个完整选中的 UV 岛 | 主界面：Compare 按钮 |
| 2 | UV Sync 开/关两种选择来源 | 不进插件界面。后端自动支持两种状态；当前状态由 Blender UV Editor 顶栏表达 |
| 3 | 8 种方向关系识别 | 主界面：MATCH 时显示短关系名（映射表见第 3 节） |
| 4 | 忽略平移/不忽略缩放形变拓扑 | 不进界面（README/文档层面的事） |
| 5 | tolerance 1e-8…1e-2，默认 1e-5 | 仅 Advanced 子面板（折叠） |
| 6 | NONE/MATCH/NO_MATCH/ERROR 四态 | 主界面：NONE 为一行 INFO 提示；其余状态使用结果 box（第 4 节） |
| 7 | 错误详情（无 UV Map、岛数量≠2 含具体数量） | 主界面：仅错误时显示，alert 红字；面数/loop 数不同属 NO_MATCH，原因作为结果区第二行 |
| 8 | max UV difference | 完全不进插件界面，也不进入 operator `self.report()` 状态栏消息 |
| 9 | 高频重复比较 | 每次点击先给 1.2 秒 `Updated` 反馈，再恢复并持久显示最新结果 |
| 10 | 只读检查、不改 UV | 无需界面表达 |

---

## 3. 精确文案（全部，含字符数预算）

面板宽约 300–360px，单行安全上限按 **≤40 字符** 控制；下表所有字符串均已满足。

### 3.1 固定文案

| 位置 | 文案 | 说明 |
|------|------|------|
| 按钮 | `Compare Selected Islands`（icon `VIEWZOOM`） | 沿用现名 |
| NONE 单行（无 box） | `Results will appear here`（icon `INFO`） | 第一次比较后原位替换为结果 box |
| NO_MATCH 第一行 | `No match`（icon `X`） | |
| ERROR 第一行（红） | `Cannot compare`（icon `ERROR`） | |
| Advanced 子面板标题 | `Advanced` | |
| Tolerance 属性 | `Tolerance` | 现有 prop，原样移入 |
| 刷新反馈 | `Updated`（icon `FILE_REFRESH`） | 每次比较后在结果框原位显示 1.2 秒 |

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

### 3.4 Advanced 子面板

只显示 `Tolerance` 属性，不显示任何比较结果或科学计数法数值。

---

## 4. 状态渲染规则

| 状态 | 第一行 | 第二行 | alert |
|------|--------|--------|-------|
| NONE | 无 box；`INFO` + `Results will appear here` | 无 | 否 |
| MATCH | `CHECKMARK` + `Match — <关系>` | 无 | 否 |
| NO_MATCH | `X` + `No match` | 原因（普通色，缩进对齐） | 否 |
| ERROR | `ERROR` + `Cannot compare` | 原因（普通色，缩进对齐） | **仅第一行** `alert=True` |

- MATCH **不做绿色**：Blender Python 无法控制 label 颜色，唯一颜色杠杆是 `row.alert`（主题红）。绿色不可行也不必要，`CHECKMARK` 图标已足够。
- NO_MATCH 不用红：它是合法结论而非用户错误；红只留给 ERROR。
- 结果持久：任何选择/状态变化不清空结果区，只有再次执行 operator 才更新（与后端现状一致）。
- 每次 operator 完成后，结果框先显示 `FILE_REFRESH · Updated` 1.2 秒，再恢复 status 对应内容；有 detail 的两行结果在刷新期间保留空的第二行，使 box 高度不跳动。
- 快速连续点击把 `WindowManager` 中的 monotonic 时间戳更新为最新值；timer 每次根据最新时间戳判断，不使用旧回调直接清状态。
- operator `poll` 失败（非编辑态网格）时按钮由 Blender 自动置灰，无需额外处理。

---

## 5. 对当前界面（截图）的删除/合并清单

| 现有元素 | 处置 |
|---------|------|
| 常驻 `Select two complete UV islands.` label | **删除**，NONE 态改为一行 `Results will appear here` |
| `UV Sync: using …` 独立 box | **完全删除**。插件自动兼容两种状态，Blender 顶栏已有状态显示 |
| 主界面 Tolerance box | **移入** Advanced 子面板（`DEFAULT_CLOSED`） |
| `Last Result` 结果 box 标题行 | **删除**，状态图标直接放在结论文案行 |
| `textwrap.wrap(message, 38)` 整段消息 | **删除**——它正是 “`(ma…` / `difference 1.13e-07).`” 断行丑态的根源；改为结构化的“结论行 + 可选原因行”，不再显示完整后端句子 |
| `(max UV difference 1.13e-07)` | **从所有插件界面与状态栏 report 完全移除** |

存储相应调整：只保留状态、headline、detail；operator 不调用 `self.report()`。

---

## 6. HTML 视觉结构 → Blender Python layout API 映射（Variant B 逐项）

### 6.0 存储（WindowManager 属性）

| HTML 数据源 | Blender |
|-------------|---------|
| `state.last.status` | `wm.rizum_uv_compare_last_status`（Enum，现有，保留） |
| `state.last.headline` | `wm.rizum_uv_compare_last_headline`（新增 `StringProperty`，`options={'HIDDEN'}`，默认 `""`） |
| `state.last.detail` | `wm.rizum_uv_compare_last_detail`（新增，同上） |
| `state.refreshFlash` | `wm["rizum_uv_compare_refresh_started"]`（临时 monotonic 时间戳，不注册为持久 RNA 属性） |
| `state.tolerance` | `wm.rizum_uv_compare_tolerance`（现有 FloatProperty，不动） |

`store_result()` 写 status/headline/detail；`compare_islands`/`compare_selected_islands` 不再向 UI 返回 max difference。

### 6.1 主面板 `UV_PT_rizum_compare.draw()` 自上而下

| # | HTML 元素 | Blender 调用 |
|---|-----------|--------------|
| 1 | 大 Compare 按钮（`.op.big`，30px 高） | `col = layout.column(); col.scale_y = 1.3; col.operator("uv.rizum_compare_islands", text="Compare Selected Islands", icon='VIEWZOOM')` |
| 2 | 初始提示或结果 `.box` | 若 status 为 NONE：`layout.label(text="Results will appear here", icon='INFO')`，**不创建 box**；否则 `box = layout.box()` 并按状态分支： |
| 2b | MATCH 一行 | `box.label(text=wm.rizum_uv_compare_last_headline, icon='CHECKMARK')` |
| 2c | NO_MATCH 两行 | `box.label(text="No match", icon='X')`；若 detail 非空：`box.label(text=wm.rizum_uv_compare_last_detail)`（原生无法缩进第二行，直接齐行即可） |
| 2d | ERROR 两行 | `row = box.row(); row.alert = True; row.label(text="Cannot compare", icon='ERROR')`；detail 非空则 `box.label(text=detail)`（**不加** alert） |
| 2e | 刚完成比较 | 若 `time.monotonic() - wm["rizum_uv_compare_refresh_started"] < 1.2`：结果第一行临时画 `box.label(text="Updated", icon='FILE_REFRESH')`；有 detail 时再画一行空 label 保持高度。此分支优先于 MATCH/NO_MATCH/ERROR |
| 3 | Advanced 子面板 | 新建 `UV_PT_rizum_compare_advanced(bpy.types.Panel)`：`bl_parent_id = "UV_PT_rizum_compare"`，`bl_label = "Advanced"`，`bl_options = {'DEFAULT_CLOSED'}`，space/region/category/poll 与主面板相同。Blender 自绘三角与开合状态，不用自定义 disclosure |
| 3a | Tolerance 行 | 子面板内：`layout.prop(wm, "rizum_uv_compare_tolerance", text="Tolerance")` |
| — | HTML 里的 `RECOMMENDED` 角标、切换器、评审控件、SVG 画布 | 均不进入插件 |

### 6.2 其余变体（未采用，仅说明结构差异）

- **A**：主面板 draw 顺序为 `layout.label(icon='UV')` 提示 → tolerance prop → `scale_y=1.3` 按钮 → 结果 box；无子面板。若实现，全部用上表同款调用，仅顺序不同。
- **C**：结果 box 置顶 → 普通高度按钮（不设 `scale_y`）→ `bl_parent_id` 子面板改名 `Details`，内容仅 tolerance。

### 6.3 明确不做的事

- 不自定义颜色/字体/圆角/阴影/hover 动画；不用 GPU canvas、自定义绘制或图标资源。
- 不给结果区加绿/黄配色；不试图让 label 自动换行（所有文案已按 ≤40 字符预裁）。
- 不显示或控制 Sync；插件界面不显示任何科学计数法数值。
- 不调用 `self.report`；不使用时间戳文案、累计次数或改变按钮文字。
- `bpy.app.timers` 只负责定时 `area.tag_redraw()`；是否仍处于 1.2 秒刷新窗口始终以最新 monotonic 时间戳为准。
