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
        assert hasattr(bpy.types.WindowManager, "rizum_uv_compare_auto")
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
        assert "FILE_REFRESH" in panel_source
        assert "Auto Compare" in panel_source
        assert 'icon="AUTO"' in panel_source
        assert "toggle=True" in panel_source
        operator_source = inspect.getsource(addon.UV_OT_rizum_compare_islands.execute)
        assert "self.report" not in operator_source

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

        wm[addon.RESULT_REFRESH_KEY] = 100.0
        assert addon.RESULT_REFRESH_SECONDS == 0.4
        assert addon.result_refresh_active(wm, now=100.0)
        assert addon.result_refresh_active(wm, now=100.399)
        assert not addon.result_refresh_active(wm, now=100.4)
        assert not addon.result_refresh_active(wm, now=99.9)

        addon.begin_result_refresh(wm)
        assert addon.result_refresh_active(wm)
        assert bpy.app.timers.is_registered(addon.result_refresh_timer)
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


def test_auto_compare_mode(addon):
    mesh = bpy.data.meshes.new("RizumAutoCompareMesh")
    obj = bpy.data.objects.new("RizumAutoCompareObject", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.from_pydata(
        (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (3.0, 1.0, 0.0),
            (2.0, 1.0, 0.0),
        ),
        (),
        ((0, 1, 2, 3), (4, 5, 6, 7)),
    )
    uv_map = mesh.uv_layers.new(name="UVMap")
    uv_sets = (
        ((0.0, 0.0), (0.2, 0.0), (0.2, 0.2), (0.0, 0.2)),
        ((0.4, 0.0), (0.6, 0.0), (0.6, 0.2), (0.4, 0.2)),
    )
    for polygon, coordinates in zip(mesh.polygons, uv_sets):
        for loop_index, coordinate in zip(polygon.loop_indices, coordinates):
            uv_map.data[loop_index].uv = coordinate

    addon.register()
    try:
        for selected in bpy.context.selected_objects:
            selected.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.context.scene.tool_settings.use_uv_select_sync = False

        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.active
        set_uv_selected(bm.faces[0], uv_layer, True)
        set_uv_selected(bm.faces[1], uv_layer, True)
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        del bm, uv_layer

        wm = bpy.context.window_manager
        assert bpy.ops.uv.rizum_compare_islands() == {"FINISHED"}
        assert wm.rizum_uv_compare_last_status == "MATCH"
        wm.rizum_uv_compare_auto = True
        assert bpy.app.timers.is_registered(addon.auto_compare_timer)
        assert addon.auto_compare_timer() == addon.AUTO_COMPARE_INTERVAL
        assert wm.rizum_uv_compare_last_status == "MATCH"
        assert wm.rizum_uv_compare_last_headline == "Match — Same orientation"
        assert not addon.auto_compare_current_selection(bpy.context)

        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.active
        set_uv_selected(bm.faces[1], uv_layer, False)
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        assert not addon.auto_compare_current_selection(bpy.context)
        assert addon.AUTO_COMPARE_SIGNATURE_KEY not in wm

        set_uv_selected(bm.faces[1], uv_layer, True)
        bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)
        assert addon.auto_compare_current_selection(bpy.context)

        wm.rizum_uv_compare_auto = False
        assert not bpy.app.timers.is_registered(addon.auto_compare_timer)
    finally:
        wm = bpy.context.window_manager
        if getattr(wm, "rizum_uv_compare_auto", False):
            wm.rizum_uv_compare_auto = False
        if obj.mode == "EDIT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(mesh)
        addon.unregister()


addon = load_addon()
test_sync_selection(addon)
test_tolerance_without_rounding_bins(addon)
test_mirror_and_real_deformation(addon)
test_panel_state_registration(addon)
test_structured_copy_contract(addon)
test_auto_compare_mode(addon)
print("RIZUM_UV_COMPARE_TESTS_OK")
