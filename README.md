<div align="center">

# Rizum Blender UV Compare

**Exact UV-island comparison for Blender, including mirrored and rotated matches.**

[![Version](https://img.shields.io/badge/version-0.1.0-7c3aed.svg)](#)
[![Blender](https://img.shields.io/badge/Blender-4.2%2B-f5792a.svg)](https://www.blender.org/)
[![License](https://img.shields.io/badge/license-GPL--3.0--or--later-2563eb.svg)](LICENSE)

[English](#english) · [中文](#中文)

</div>

---

## English

Blender can make two UV islands look almost identical without proving that every UV vertex, edge, and face really matches. This small script compares exactly two selected UV islands and reports their relationship.

### What it detects

- Same orientation
- Horizontal or vertical mirror
- 90° or 180° rotation
- Mirror across either diagonal
- No exact match

Translation is ignored. Scale and deformation are not ignored. The default tolerance is `1e-5`.

### Usage

1. Download [`uv_exact_compare.py`](uv_exact_compare.py).
2. In Blender, enter **Edit Mode** on the mesh.
3. Open the UV Editor and turn **UV Sync Selection off**.
4. Select exactly two complete UV islands.
5. Open the script in Blender's Text Editor and choose **Run Script** (`Alt+P`).
6. Read the result in the popup and the system console.

The script operates on the active edit mesh. Both islands must be fully selected and use the same face layout to count as an exact match.

### Why this exists

It was made for checking front/back UV shells that share the same topology but may be mirrored in 3D. It is useful when snapping by eye or an add-on's copy/paste result is ambiguous.

## 中文

Blender 里两个 UV 岛看起来可以几乎一样，但肉眼很难确认每个 UV 顶点、边和面是否真的完全一致。这个小脚本会比较两个选中的完整 UV 岛，并直接报告它们之间的关系。

### 可以识别

- 同方向完全一致
- 水平或垂直镜像
- 旋转 90° 或 180°
- 沿两条对角线镜像
- 不完全一致

比较时忽略整体平移，但不会忽略缩放和形变。默认容差为 `1e-5`。

### 使用方法

1. 下载 [`uv_exact_compare.py`](uv_exact_compare.py)。
2. 在 Blender 中选中网格并进入**编辑模式**。
3. 打开 UV 编辑器，关闭 **UV Sync Selection（同步选择）**。
4. 完整选中且只选中两个 UV 岛。
5. 在 Blender 文本编辑器中打开脚本，点击 **Run Script**，或按 `Alt+P`。
6. 弹窗和系统控制台会显示比较结果。

脚本只检查当前正在编辑的网格。两个 UV 岛必须完整选中，而且面布局相同，才可能判定为完全一致。

### 适用场景

用于检查布线一致、但 3D 朝向相反的正面/背面 UV 岛。尤其适合判断它们是否能够精确叠放，以及插件复制粘贴结果是否真的改变了 UV。

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
