# Changelog

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
