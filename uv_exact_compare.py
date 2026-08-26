# SPDX-License-Identifier: GPL-3.0-or-later

"""Rizum UV Compare — exact comparison of two selected UV islands."""

bl_info = {
    "name": "Rizum UV Compare",
    "author": "Rizumu85",
    "version": (0, 5, 1),
    "blender": (4, 2, 0),
    "location": "UV Editor > Sidebar > UV Compare",
    "description": "Compare two UV islands for exact mirrored or rotated matches",
    "category": "UV",
}

from collections import defaultdict, deque
import math
import time
from typing import NamedTuple

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty


DEFAULT_TOLERANCE = 1.0e-5
RESULT_REFRESH_SECONDS = 0.4
RESULT_REFRESH_INTERVAL = 0.1
RESULT_REFRESH_KEY = "rizum_uv_compare_refresh_started"
AUTO_COMPARE_INTERVAL = 0.25
AUTO_COMPARE_SIGNATURE_KEY = "rizum_uv_compare_auto_signature"

TRANSFORMS = (
    ("Same orientation", lambda x, y: (x, y)),
    ("Mirrored horizontally (X)", lambda x, y: (-x, y)),
    ("Mirrored vertically (Y)", lambda x, y: (x, -y)),
    ("Rotated 180°", lambda x, y: (-x, -y)),
    ("Rotated 90° counter-clockwise", lambda x, y: (-y, x)),
    ("Rotated 90° clockwise", lambda x, y: (y, -x)),
    ("Mirrored across X=Y", lambda x, y: (y, x)),
    ("Mirrored across X=-Y", lambda x, y: (-y, -x)),
)

TRANSFORM_DISPLAY_NAMES = {
    "Same orientation": "Same orientation",
    "Mirrored horizontally (X)": "Mirrored horizontally",
    "Mirrored vertically (Y)": "Mirrored vertically",
    "Rotated 180°": "Rotated 180°",
    "Rotated 90° counter-clockwise": "Rotated 90° CCW",
    "Rotated 90° clockwise": "Rotated 90° CW",
    "Mirrored across X=Y": "Mirrored diagonally (X=Y)",
    "Mirrored across X=-Y": "Mirrored diagonally (X=-Y)",
}

RESULT_STATUS_ITEMS = (
    ("NONE", "None", "No comparison has been run"),
    ("MATCH", "Match", "The islands are an exact match"),
    ("NO_MATCH", "No Match", "The islands are not an exact match"),
    ("ERROR", "Error", "The selection cannot be compared"),
)


class CompareResult(NamedTuple):
    status: str
    message: str
    headline: str
    detail: str


def uv_selected(loop, uv_layer):
    """Support the UV-selection API used by Blender 4.2 and 5.x."""
    if hasattr(loop, "uv_select_vert"):
        return loop.uv_select_vert
    return loop[uv_layer].select


def close_uv(a, b, tolerance):
    return abs(a.x - b.x) <= tolerance and abs(a.y - b.y) <= tolerance


def face_fully_selected(face, uv_layer, use_uv_select_sync):
    """Read a complete face selection in either Blender UV selection mode."""
    if use_uv_select_sync:
        return (
            face.select
            or all(vert.select for vert in face.verts)
            or all(edge.select for edge in face.edges)
        )
    return face.select and all(uv_selected(loop, uv_layer) for loop in face.loops)


def selected_uv_islands(bm, uv_layer, tolerance, use_uv_select_sync=False):
    """Return connected components made from fully selected UV faces."""
    faces = [
        face
        for face in bm.faces
        if face_fully_selected(face, uv_layer, use_uv_select_sync)
    ]
    face_set = set(faces)
    adjacency = defaultdict(set)
    edge_uses = defaultdict(list)

    for face in faces:
        for loop in face.loops:
            next_loop = loop.link_loop_next
            edge_uses[loop.edge].append(
                (
                    face,
                    {
                        loop.vert: loop[uv_layer].uv.copy(),
                        next_loop.vert: next_loop[uv_layer].uv.copy(),
                    },
                )
            )

    for uses in edge_uses.values():
        if len(uses) != 2:
            continue
        (face_a, map_a), (face_b, map_b) = uses
        if face_a not in face_set or face_b not in face_set:
            continue
        shared = set(map_a) & set(map_b)
        if len(shared) == 2 and all(
            close_uv(map_a[vert], map_b[vert], tolerance) for vert in shared
        ):
            adjacency[face_a].add(face_b)
            adjacency[face_b].add(face_a)

    unseen = set(faces)
    islands = []
    while unseen:
        root = unseen.pop()
        island = {root}
        queue = deque([root])
        while queue:
            face = queue.popleft()
            for neighbor in adjacency[face]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    island.add(neighbor)
                    queue.append(neighbor)
        islands.append(island)
    return islands


def island_features(island, uv_layer, transform):
    """Build translation-independent point, edge and face geometry."""
    raw_loops = []
    raw_edges = []
    raw_faces = []

    for face in island:
        face_points = []
        for loop in face.loops:
            uv = loop[uv_layer].uv
            point = transform(uv.x, uv.y)
            next_uv = loop.link_loop_next[uv_layer].uv
            next_point = transform(next_uv.x, next_uv.y)
            raw_loops.append(point)
            raw_edges.append((point, next_point))
            face_points.append(point)
        raw_faces.append(face_points)

    center_x = sum(point[0] for point in raw_loops) / len(raw_loops)
    center_y = sum(point[1] for point in raw_loops) / len(raw_loops)

    def normalize(point):
        return point[0] - center_x, point[1] - center_y

    return (
        [normalize(point) for point in raw_loops],
        [(normalize(a), normalize(b)) for a, b in raw_edges],
        [[normalize(point) for point in face] for face in raw_faces],
    )


def point_distance(point_a, point_b):
    """Return Chebyshev distance in UV space."""
    return max(abs(point_a[0] - point_b[0]), abs(point_a[1] - point_b[1]))


def multiset_match_distance(items_a, items_b, distance, tolerance):
    """Return the largest paired distance, or infinity when no pairing exists."""
    if len(items_a) != len(items_b):
        return math.inf
    if not items_a:
        return 0.0

    # Most UV islands have a stable lexicographic order. This avoids building a
    # large matching graph for common grids and for repeated/coincident points.
    ordered_deltas = [
        distance(item_a, item_b)
        for item_a, item_b in zip(sorted(items_a), sorted(items_b))
    ]
    if max(ordered_deltas) <= tolerance:
        return max(ordered_deltas)

    candidates = []
    for item_a in items_a:
        choices = []
        for index_b, item_b in enumerate(items_b):
            delta = distance(item_a, item_b)
            if delta <= tolerance:
                choices.append((delta, index_b))
        if not choices:
            return math.inf
        choices.sort()
        candidates.append(choices)

    # Fewest candidates first makes the augmenting-path match both fast and stable.
    order = sorted(range(len(items_a)), key=lambda index: len(candidates[index]))
    matched_b = {}

    def assign(index_a, visited_b):
        for _delta, index_b in candidates[index_a]:
            if index_b in visited_b:
                continue
            visited_b.add(index_b)
            previous_a = matched_b.get(index_b)
            if previous_a is None or assign(previous_a, visited_b):
                matched_b[index_b] = index_a
                return True
        return False

    for index_a in order:
        if not assign(index_a, set()):
            return math.inf

    return max(
        distance(items_a[index_a], items_b[index_b])
        for index_b, index_a in matched_b.items()
    )


def edge_distance(edge_a, edge_b):
    direct = max(
        point_distance(edge_a[0], edge_b[0]),
        point_distance(edge_a[1], edge_b[1]),
    )
    reversed_order = max(
        point_distance(edge_a[0], edge_b[1]),
        point_distance(edge_a[1], edge_b[0]),
    )
    return min(direct, reversed_order)


def face_distance(face_a, face_b, tolerance):
    return multiset_match_distance(face_a, face_b, point_distance, tolerance)


def feature_match_distance(features_a, features_b, tolerance):
    loops_a, edges_a, faces_a = features_a
    loops_b, edges_b, faces_b = features_b
    loop_error = multiset_match_distance(
        loops_a, loops_b, point_distance, tolerance
    )
    if math.isinf(loop_error):
        return math.inf
    edge_error = multiset_match_distance(
        edges_a, edges_b, edge_distance, tolerance
    )
    if math.isinf(edge_error):
        return math.inf
    face_error = multiset_match_distance(
        faces_a,
        faces_b,
        lambda face_a, face_b: face_distance(face_a, face_b, tolerance),
        tolerance,
    )
    return max(loop_error, edge_error, face_error)


def compare_islands(island_a, island_b, uv_layer, tolerance):
    """Compare two UV islands and return a structured result for the panel."""
    if len(island_a) != len(island_b):
        message = f"Different face counts: {len(island_a)} vs {len(island_b)}."
        return CompareResult(
            "NO_MATCH",
            message,
            "No match",
            f"Different face counts ({len(island_a)} vs {len(island_b)}).",
        )

    loop_count_a = sum(len(face.loops) for face in island_a)
    loop_count_b = sum(len(face.loops) for face in island_b)
    if loop_count_a != loop_count_b:
        message = f"Different UV loop counts: {loop_count_a} vs {loop_count_b}."
        return CompareResult(
            "NO_MATCH",
            message,
            "No match",
            f"Different UV loop counts ({loop_count_a} vs {loop_count_b}).",
        )

    features_a = island_features(island_a, uv_layer, TRANSFORMS[0][1])
    for label, transform in TRANSFORMS:
        features_b = island_features(island_b, uv_layer, transform)
        error = feature_match_distance(features_a, features_b, tolerance)
        if error <= tolerance:
            message = f"Exact match: {label}."
            return CompareResult(
                "MATCH",
                message,
                f"Match — {TRANSFORM_DISPLAY_NAMES[label]}",
                "",
            )

    message = f"Not a match within tolerance {tolerance:g}."
    return CompareResult(
        "NO_MATCH",
        message,
        "No match",
        "Islands differ beyond tolerance.",
    )


def selected_uv_data(obj, tolerance, use_uv_select_sync=False):
    """Return the live edit BMesh, active UV layer and selected UV islands."""
    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        return bm, None, []

    bm.faces.index_update()
    islands = selected_uv_islands(
        bm, uv_layer, tolerance, use_uv_select_sync=use_uv_select_sync
    )
    return bm, uv_layer, islands


def compare_selected_islands(obj, tolerance, use_uv_select_sync=False):
    """Return a structured result for the current UV selection."""
    bm, uv_layer, islands = selected_uv_data(
        obj,
        tolerance,
        use_uv_select_sync=use_uv_select_sync,
    )
    if uv_layer is None:
        message = "The active mesh has no UV map."
        return CompareResult("ERROR", message, "Cannot compare", message)

    if len(islands) != 2:
        message = f"Select exactly two complete UV islands (found {len(islands)})."
        return CompareResult(
            "ERROR",
            message,
            "Cannot compare",
            f"Found {len(islands)} islands, need exactly 2.",
        )

    island_a, island_b = islands
    return compare_islands(island_a, island_b, uv_layer, tolerance)


def store_result(context, result):
    wm = context.window_manager
    wm.rizum_uv_compare_last_status = result.status
    wm.rizum_uv_compare_last_headline = result.headline
    wm.rizum_uv_compare_last_detail = result.detail


def result_refresh_active(wm, now=None):
    """Return whether the result box is inside its short refresh window."""
    started = wm.get(RESULT_REFRESH_KEY)
    if started is None:
        return False
    if now is None:
        now = time.monotonic()
    elapsed = now - float(started)
    return 0.0 <= elapsed < RESULT_REFRESH_SECONDS


def tag_uv_compare_areas(wm):
    """Redraw UV/Image Editors that can contain the add-on panel."""
    for window in wm.windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type == "IMAGE_EDITOR":
                area.tag_redraw()


def result_refresh_timer():
    wm = getattr(bpy.context, "window_manager", None)
    if wm is None:
        return None
    tag_uv_compare_areas(wm)
    if result_refresh_active(wm):
        return RESULT_REFRESH_INTERVAL
    return None


def begin_result_refresh(wm):
    """Restart the refresh pulse without allowing an older timer to end it."""
    wm[RESULT_REFRESH_KEY] = time.monotonic()
    tag_uv_compare_areas(wm)
    if not bpy.app.timers.is_registered(result_refresh_timer):
        bpy.app.timers.register(
            result_refresh_timer,
            first_interval=RESULT_REFRESH_INTERVAL,
        )


def clear_auto_compare_signature(wm):
    if AUTO_COMPARE_SIGNATURE_KEY in wm:
        del wm[AUTO_COMPARE_SIGNATURE_KEY]


def auto_compare_signature(obj, uv_layer, islands, tolerance, use_uv_select_sync):
    """Build a stable identity for one complete two-island selection."""
    if len(islands) != 2:
        return None
    face_groups = tuple(
        sorted(tuple(sorted(face.index for face in island)) for island in islands)
    )
    return "|".join(
        (
            str(obj.as_pointer()),
            uv_layer.name,
            "1" if use_uv_select_sync else "0",
            format(tolerance, ".17g"),
            repr(face_groups),
        )
    )


def auto_compare_current_selection(context):
    """Compare once when the current valid two-island selection is new."""
    wm = getattr(context, "window_manager", None)
    obj = getattr(context, "edit_object", None)
    if wm is None or obj is None or obj.type != "MESH":
        if wm is not None:
            clear_auto_compare_signature(wm)
        return False

    tolerance = wm.rizum_uv_compare_tolerance
    use_uv_select_sync = context.scene.tool_settings.use_uv_select_sync
    bm, uv_layer, islands = selected_uv_data(
        obj,
        tolerance,
        use_uv_select_sync=use_uv_select_sync,
    )
    signature = (
        auto_compare_signature(
            obj,
            uv_layer,
            islands,
            tolerance,
            use_uv_select_sync,
        )
        if uv_layer is not None
        else None
    )
    if signature is None:
        clear_auto_compare_signature(wm)
        return False
    if wm.get(AUTO_COMPARE_SIGNATURE_KEY) == signature:
        return False

    wm[AUTO_COMPARE_SIGNATURE_KEY] = signature
    island_a, island_b = islands
    result = compare_islands(island_a, island_b, uv_layer, tolerance)
    store_result(context, result)
    begin_result_refresh(wm)
    print(f"Rizum UV Compare (Auto): {result.message} (tolerance {tolerance:g})")
    return True


def auto_compare_timer():
    context = bpy.context
    wm = getattr(context, "window_manager", None)
    if wm is None or not getattr(wm, "rizum_uv_compare_auto", False):
        return None
    try:
        auto_compare_current_selection(context)
    except (AttributeError, ReferenceError, RuntimeError, ValueError):
        clear_auto_compare_signature(wm)
    return AUTO_COMPARE_INTERVAL


def update_auto_compare(wm, context):
    """Start or stop the lightweight selection watcher."""
    clear_auto_compare_signature(wm)
    if wm.rizum_uv_compare_auto:
        if not bpy.app.timers.is_registered(auto_compare_timer):
            bpy.app.timers.register(auto_compare_timer, first_interval=0.05)
    elif bpy.app.timers.is_registered(auto_compare_timer):
        bpy.app.timers.unregister(auto_compare_timer)
    tag_uv_compare_areas(wm)


class UV_OT_rizum_compare_islands(bpy.types.Operator):
    bl_idname = "uv.rizum_compare_islands"
    bl_label = "Compare Selected Islands"
    bl_description = "Check whether two selected UV islands match exactly"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        obj = context.edit_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context):
        tolerance = context.window_manager.rizum_uv_compare_tolerance
        use_uv_select_sync = context.scene.tool_settings.use_uv_select_sync
        result = compare_selected_islands(
            context.edit_object,
            tolerance,
            use_uv_select_sync=use_uv_select_sync,
        )
        store_result(context, result)
        begin_result_refresh(context.window_manager)

        print(f"Rizum UV Compare: {result.message} (tolerance {tolerance:g})")
        return {"CANCELLED"} if result.status == "ERROR" else {"FINISHED"}


class UV_PT_rizum_compare(bpy.types.Panel):
    bl_label = "Rizum UV Compare"
    bl_idname = "UV_PT_rizum_compare"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "UV Compare"

    @classmethod
    def poll(cls, context):
        return getattr(context.area, "ui_type", None) == "UV"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        layout.prop(
            wm,
            "rizum_uv_compare_auto",
            text="Auto Compare",
            icon="AUTO",
            toggle=True,
        )

        action = layout.column()
        action.scale_y = 1.3
        action.operator(
            "uv.rizum_compare_islands",
            text="Compare Selected Islands",
            icon="VIEWZOOM",
        )

        status = wm.rizum_uv_compare_last_status
        if status == "NONE":
            layout.label(text="Results will appear here", icon="INFO")
            return

        result_box = layout.box()
        if result_refresh_active(wm):
            result_box.label(text="Updated", icon="FILE_REFRESH")
            if wm.rizum_uv_compare_last_detail:
                result_box.label(text="")
            return

        if status == "MATCH":
            result_box.label(
                text=wm.rizum_uv_compare_last_headline,
                icon="CHECKMARK",
            )
        elif status == "NO_MATCH":
            result_box.label(text="No match", icon="X")
            if wm.rizum_uv_compare_last_detail:
                result_box.label(text=wm.rizum_uv_compare_last_detail)
        else:
            error_row = result_box.row()
            error_row.alert = True
            error_row.label(text="Cannot compare", icon="ERROR")
            if wm.rizum_uv_compare_last_detail:
                result_box.label(text=wm.rizum_uv_compare_last_detail)

class UV_PT_rizum_compare_advanced(bpy.types.Panel):
    bl_label = "Advanced"
    bl_idname = "UV_PT_rizum_compare_advanced"
    bl_parent_id = "UV_PT_rizum_compare"
    bl_space_type = "IMAGE_EDITOR"
    bl_region_type = "UI"
    bl_category = "UV Compare"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return getattr(context.area, "ui_type", None) == "UV"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.prop(wm, "rizum_uv_compare_tolerance", text="Tolerance")


CLASSES = (
    UV_OT_rizum_compare_islands,
    UV_PT_rizum_compare,
    UV_PT_rizum_compare_advanced,
)


def register():
    bpy.types.WindowManager.rizum_uv_compare_auto = BoolProperty(
        name="Auto Compare",
        description="Automatically compare whenever exactly two UV islands are selected",
        default=False,
        update=update_auto_compare,
    )
    bpy.types.WindowManager.rizum_uv_compare_tolerance = FloatProperty(
        name="Tolerance",
        description="Maximum UV-coordinate difference counted as equal",
        default=DEFAULT_TOLERANCE,
        min=1.0e-8,
        max=1.0e-2,
        precision=6,
    )
    bpy.types.WindowManager.rizum_uv_compare_last_headline = StringProperty(
        name="Last Headline",
        default="",
        options={"HIDDEN"},
    )
    bpy.types.WindowManager.rizum_uv_compare_last_detail = StringProperty(
        name="Last Detail",
        default="",
        options={"HIDDEN"},
    )
    bpy.types.WindowManager.rizum_uv_compare_last_status = EnumProperty(
        name="Last Status",
        items=RESULT_STATUS_ITEMS,
        default="NONE",
        options={"HIDDEN"},
    )
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    if bpy.app.timers.is_registered(auto_compare_timer):
        bpy.app.timers.unregister(auto_compare_timer)
    if bpy.app.timers.is_registered(result_refresh_timer):
        bpy.app.timers.unregister(result_refresh_timer)
    wm = getattr(bpy.context, "window_manager", None)
    if wm is not None:
        if RESULT_REFRESH_KEY in wm:
            del wm[RESULT_REFRESH_KEY]
        clear_auto_compare_signature(wm)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.rizum_uv_compare_last_status
    del bpy.types.WindowManager.rizum_uv_compare_last_detail
    del bpy.types.WindowManager.rizum_uv_compare_last_headline
    del bpy.types.WindowManager.rizum_uv_compare_tolerance
    del bpy.types.WindowManager.rizum_uv_compare_auto


if __name__ == "__main__":
    register()
