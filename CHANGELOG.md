# Changelog

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
