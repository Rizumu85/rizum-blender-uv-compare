# Changelog

## 0.5.1 — 2026-08-26

- Fixed invalid `BMFace` references that broke both manual and automatic comparison when no external edit-BMesh wrapper happened to remain alive.
- Added an operator-level regression test that releases the setup wrapper before comparing, matching real Blender usage.

## 0.5.0 — 2026-08-26

- Added an **Auto Compare** mode that watches for a new pair of two complete selected UV islands.
- Kept invalid intermediate selections silent while preserving the last result.
- Deduplicated unchanged selections and kept the manual compare button available.
- Limited the watcher to a lightweight 0.25-second interval while the mode is enabled.

## 0.4.4 — 2026-08-26

- Shortened the in-panel result refresh pulse from 1.2 seconds to 0.4 seconds for faster feedback.

## 0.4.3 — 2026-08-26

- Added a 1.2-second `FILE_REFRESH · Updated` pulse inside the persistent result box.
- Made rapid repeated comparisons restart the same refresh window safely.
- Removed operator `self.report()` feedback in favor of the in-panel refresh state.
- Preserved result-box height while two-line results are refreshing.

## 0.4.2 — 2026-08-26

- Removed maximum UV difference from the panel, Advanced sub-panel and operator reports.
- Replaced the initial empty result box with one compact `Results will appear here` info line.
- Kept Advanced focused on the tolerance setting only.

## 0.4.1 — 2026-08-26

- Removed the redundant UV Sync Selection status line from the panel.
- UV Sync on/off support remains automatic; Blender's UV Editor header already shows the current state.

## 0.4.0 — 2026-08-26

- Redesigned the panel around the frequent compare-and-check workflow.
- Moved tolerance and maximum UV difference into a collapsed **Advanced** sub-panel.
- Replaced wrapped technical messages with concise, structured verdicts and reasons.
- Reduced UV Sync Selection to a compact read-only context line.
- Added persistent structured result fields for headline, detail and technical information.

## 0.3.0 — 2026-08-26

- Added support for comparing selections while **UV Sync Selection** is enabled.
- Replaced tolerance quantization with direct tolerant point, edge and face matching.
- Fixed false negatives near rounding-bin boundaries even when the real UV difference was far below the configured tolerance.
- Added the measured maximum UV difference to successful results.
- Added Blender regression tests for sync selection, tolerance boundaries, mirrors and real deformation.

## 0.2.0 — 2026-08-26

- Added a persistent **UV Compare** sidebar panel in the UV Editor.
- Added a one-click **Compare Selected Islands** operator.
- Added an adjustable comparison tolerance.
- Added persistent display of the last result.
- Added a Blender 4.2+ extension package.

## 0.1.0 — 2026-08-26

- Added the initial Text Editor script for exact UV-island comparison.
