"""Run with: blender --background --python tests/blender_regression.py"""

import importlib.util
import inspect
from pathlib import Path
import sys

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "uv_exact_compare.py"


def load_addon():
    spec = importlib.util.spec_from_file_location("rizum_uv_compare_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_uv_faces(coordinate_sets):
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    faces = []
    for face_index, coordinates in enumerate(coordinate_sets):
        verts = [
            bm.verts.new((float(index), float(face_index), 0.0))
            for index in range(len(coordinates))
        ]
        face = bm.faces.new(verts)
        for loop, coordinate in zip(face.loops, coordinates):
            loop[uv_layer].uv = coordinate
        faces.append(face)
    return bm, uv_layer, faces


def set_uv_selected(face, uv_layer, selected):
    face.select = selected
    for vert in face.verts:
        vert.select = selected
    for edge in face.edges:
        edge.select = selected
    for loop in face.loops:
        if hasattr(loop, "uv_select_vert"):
            loop.uv_select_vert = selected
        else:
            loop[uv_layer].select = selected


def test_sync_selection(addon):
    square = ((0.0, 0.0), (0.2, 0.0), (0.2, 0.2), (0.0, 0.2))
    bm, uv_layer, faces = build_uv_faces(
        (square, tuple((x + 0.4, y) for x, y in square), square)
    )
    set_uv_selected(faces[0], uv_layer, True)
    set_uv_selected(faces[1], uv_layer, True)
    set_uv_selected(faces[2], uv_layer, False)
    assert len(addon.selected_uv_islands(bm, uv_layer, 1.0e-5, False)) == 2

    for face in faces[:2]:
        for loop in face.loops:
            if hasattr(loop, "uv_select_vert"):
                loop.uv_select_vert = False
            else:
                loop[uv_layer].select = False
    assert len(addon.selected_uv_islands(bm, uv_layer, 1.0e-5, False)) == 0
    assert len(addon.selected_uv_islands(bm, uv_layer, 1.0e-5, True)) == 2
    bm.free()


def test_tolerance_without_rounding_bins(addon):
    island_a = (
        (0.0, 0.0),
        (0.100005, 0.0),
        (0.100005, 0.2),
        (0.0, 0.2),
    )
    island_b = (
        (0.4, 0.7),
        (0.5000051125, 0.7),
        (0.5000051125, 0.9),
        (0.4, 0.9),
    )
    bm, uv_layer, faces = build_uv_faces((island_a, island_b))
    result = addon.compare_islands(
        {faces[0]}, {faces[1]}, uv_layer, addon.DEFAULT_TOLERANCE
    )
    assert result.status == "MATCH", result.message
    assert result.headline == "Match — Same orientation"
    assert result.detail == ""
    assert "difference" not in result.message.lower()
    bm.free()


def test_mirror_and_real_deformation(addon):
    source = ((0.0, 0.0), (0.3, 0.0), (0.2, 0.2), (0.0, 0.1))
    mirrored = tuple((-x + 0.8, y + 0.4) for x, y in source)
    deformed = tuple((x * 1.02 + 1.2, y) for x, y in source)
    bm, uv_layer, faces = build_uv_faces((source, mirrored, deformed))
    result = addon.compare_islands(
        {faces[0]}, {faces[1]}, uv_layer, addon.DEFAULT_TOLERANCE
    )
    assert result.status == "MATCH", result.message
    assert result.headline == "Match — Mirrored horizontally"

    result = addon.compare_islands(
        {faces[0]}, {faces[2]}, uv_layer, addon.DEFAULT_TOLERANCE
    )
    assert result.status == "NO_MATCH", result.message
    assert result.headline == "No match"
    assert result.detail == "Islands differ beyond tolerance."
    bm.free()


def test_panel_state_registration(addon):
    addon.register()
    try:
        assert hasattr(bpy.types.WindowManager, "rizum_uv_compare_last_headline")
        assert hasattr(bpy.types.WindowManager, "rizum_uv_compare_last_detail")
        assert not hasattr(bpy.types.WindowManager, "rizum_uv_compare_last_technical")
        assert not hasattr(bpy.types.WindowManager, "rizum_uv_compare_last_result")
        assert addon.UV_PT_rizum_compare_advanced.bl_parent_id == "UV_PT_rizum_compare"
        assert "DEFAULT_CLOSED" in addon.UV_PT_rizum_compare_advanced.bl_options
        panel_source = inspect.getsource(addon.UV_PT_rizum_compare.draw)
        assert "UV Sync on" not in panel_source
        assert "UV Sync off" not in panel_source
        assert "Results will appear here" in panel_source
        assert "No comparison yet" not in panel_source
        assert "Max UV difference" not in inspect.getsource(addon)

        result = addon.CompareResult(
            "MATCH",
            "Exact match.",
            "Match — Same orientation",
            "",
        )
        addon.store_result(bpy.context, result)
        wm = bpy.context.window_manager
        assert wm.rizum_uv_compare_last_status == "MATCH"
        assert wm.rizum_uv_compare_last_headline == result.headline
        assert wm.rizum_uv_compare_last_detail == result.detail
    finally:
        addon.unregister()


def test_structured_copy_contract(addon):
    transform_labels = {label for label, _transform in addon.TRANSFORMS}
    assert set(addon.TRANSFORM_DISPLAY_NAMES) == transform_labels
    assert all(
        len(f"Match — {display_name}") <= 40
        for display_name in addon.TRANSFORM_DISPLAY_NAMES.values()
    )

    quad = ((0.0, 0.0), (0.2, 0.0), (0.2, 0.2), (0.0, 0.2))
    triangle = ((0.4, 0.0), (0.6, 0.0), (0.5, 0.2))
    bm, uv_layer, faces = build_uv_faces((quad, triangle))
    result = addon.compare_islands(
        {faces[0]}, {faces[1]}, uv_layer, addon.DEFAULT_TOLERANCE
    )
    assert result.status == "NO_MATCH"
    assert result.detail == "Different UV loop counts (4 vs 3)."
    assert result.message == "Different UV loop counts: 4 vs 3."
    bm.free()


addon = load_addon()
test_sync_selection(addon)
test_tolerance_without_rounding_bins(addon)
test_mirror_and_real_deformation(addon)
test_panel_state_registration(addon)
test_structured_copy_contract(addon)
print("RIZUM_UV_COMPARE_TESTS_OK")
