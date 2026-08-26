<div align="center">

# Rizum Blender UV Compare

**Exact UV-island comparison for Blender, including mirrored and rotated matches.**

[![Version](https://img.shields.io/badge/version-0.4.3-7c3aed.svg)](https://github.com/Rizumu85/rizum-blender-uv-compare/releases/latest)
[![Blender](https://img.shields.io/badge/Blender-4.2%2B-f5792a.svg)](https://www.blender.org/)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-2563eb.svg)](LICENSE)

[English](#english) · [中文](#中文)

</div>

---

## English

Blender can make two UV islands look almost identical without proving that every UV vertex, edge, and face really matches. This add-on puts a reusable comparison button in the UV Editor sidebar and reports their exact relationship.

### What it detects

- Same orientation
- Horizontal or vertical mirror
- 90° or 180° rotation
- Mirror across either diagonal
- No exact match

Translation is ignored. Scale and deformation are not ignored. The default tolerance is `1e-5`.

### Install

1. Download the ZIP from the [latest release](https://github.com/Rizumu85/rizum-blender-uv-compare/releases/latest).
2. In Blender, open **Edit > Preferences > Add-ons**.
3. Choose **Install from Disk**, select the downloaded ZIP, and enable **Rizum UV Compare**.

You can also install [`uv_exact_compare.py`](uv_exact_compare.py) as a legacy single-file add-on, or run it once from Blender's Text Editor.

### Usage

1. Enter **Edit Mode** on the mesh and open the UV Editor.
2. Press `N` and open the **UV Compare** tab.
3. Leave **UV Sync Selection** on or off—the add-on supports both modes.
4. Select exactly two complete UV islands.
5. Press **Compare Selected Islands**.
6. Read the concise persistent result below the button. Repeat whenever needed.

Tolerance lives in the collapsed **Advanced** sub-panel so the repeat workflow stays compact. Maximum UV difference is intentionally not shown in the interface.

Every comparison briefly changes the persistent result box to **Updated** for 1.2 seconds, so repeating an unchanged result still gives visible feedback without status-bar reports.

The script operates on the active edit mesh. Both islands must be fully selected and use the same face layout to count as an exact match.

### Why this exists

It was made for checking front/back UV shells that share the same topology but may be mirrored in 3D. It is useful when snapping by eye or an add-on's copy/paste result is ambiguous.

## 中文

Blender 里两个 UV 岛看起来可以几乎一样，但肉眼很难确认每个 UV 顶点、边和面是否真的完全一致。这个插件会在 UV 编辑器右侧栏提供一个可重复使用的比较按钮，并直接报告两个 UV 岛之间的精确关系。

### 可以识别

- 同方向完全一致
- 水平或垂直镜像
- 旋转 90° 或 180°
- 沿两条对角线镜像
- 不完全一致

比较时忽略整体平移，但不会忽略缩放和形变。默认容差为 `1e-5`。

### 安装

1. 从 [Releases](https://github.com/Rizumu85/rizum-blender-uv-compare/releases/latest) 下载插件 ZIP。
2. 在 Blender 打开 **编辑 > 偏好设置 > 插件**。
3. 选择 **Install from Disk（从磁盘安装）**，选择 ZIP，并启用 **Rizum UV Compare**。

也可以把 [`uv_exact_compare.py`](uv_exact_compare.py) 当作传统单文件插件安装，或在 Blender 文本编辑器中运行一次。

### 使用方法

1. 选中网格进入**编辑模式**，并打开 UV 编辑器。
2. 按 `N`，进入 **UV Compare** 标签。
3. **UV Sync Selection（同步选择）**可以开启或关闭，插件支持两种模式。
4. 完整选中且只选中两个 UV 岛。
5. 点击 **Compare Selected Islands**。
6. 按钮下方会保留简洁的上一次结果，可以换一组 UV 后继续点击。

Tolerance 收在默认折叠的 **Advanced** 子面板中；最大 UV 差值不在界面中显示，主界面只保留高频操作需要的信息。

每次比较后，持久结果框会短暂显示 1.2 秒 **Updated**，因此即使连续得到相同结果，也能确认插件已经重新执行；无需状态栏报告。

脚本只检查当前正在编辑的网格。两个 UV 岛必须完整选中，而且面布局相同，才可能判定为完全一致。

### 适用场景

用于检查布线一致、但 3D 朝向相反的正面/背面 UV 岛。尤其适合判断它们是否能够精确叠放，以及插件复制粘贴结果是否真的改变了 UV。

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
