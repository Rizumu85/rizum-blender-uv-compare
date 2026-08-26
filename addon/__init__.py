# SPDX-License-Identifier: GPL-3.0-or-later

"""Rizum UV Compare — exact comparison of two selected UV islands."""

bl_info = {
    "name": "Rizum UV Compare",
    "author": "Rizumu85",
    "version": (0, 2, 0),
    "blender": (4, 2, 0),
    "location": "UV Editor > Sidebar > UV Compare",
    "description": "Compare two UV islands for exact mirrored or rotated matches",
    "category": "UV",
}

from collections import Counter, defaultdict, deque
import textwrap

import bmesh
import bpy
from bpy.props import EnumProperty, FloatProperty, StringProperty


DEFAULT_TOLERANCE = 1.0e-5

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

RESULT_STATUS_ITEMS = (
    ("NONE", "None", "No comparison has been run"),
    ("MATCH", "Match", "The islands are an exact match"),
    ("NO_MATCH", "No Match", "The islands are not an exact match"),
    ("ERROR", "Error", "The selection cannot be compared"),
)


def uv_selected(loop, uv_layer):
    """Support the UV-selection API used by Blender 4.2 and 5.x."""
    if hasattr(loop, "uv_select_vert"):
        return loop.uv_select_vert
    return loop[uv_layer].select


def close_uv(a, b, tolerance):
    return abs(a.x - b.x) <= tolerance and abs(a.y - b.y) <= tolerance


def selected_uv_islands(bm, uv_layer, tolerance):
    """Return connected components made from fully selected UV faces."""
    faces = [
        face
        for face in bm.faces
        if face.select and all(uv_selected(loop, uv_layer) for loop in face.loops)
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


def island_signature(island, uv_layer, transform, tolerance):
    """Build a translation-independent signature of UV vertices, edges and faces."""
    raw_points = []
    raw_edges = []
    raw_faces = []

    for face in island:
        face_points = []
        for loop in face.loops:
            uv = loop[uv_layer].uv
            point = transform(uv.x, uv.y)
            next_uv = loop.link_loop_next[uv_layer].uv
            next_point = transform(next_uv.x, next_uv.y)
            raw_points.extend((point, next_point))
            raw_edges.append((point, next_point))
            face_points.append(point)
        raw_faces.append(face_points)

    min_x = min(point[0] for point in raw_points)
    min_y = min(point[1] for point in raw_points)

    def quantize(point):
        return (
            round((point[0] - min_x) / tolerance),
            round((point[1] - min_y) / tolerance),
        )

    vertices = frozenset(quantize(point) for point in raw_points)
    edges = Counter(tuple(sorted((quantize(a), quantize(b)))) for a, b in raw_edges)
    faces = Counter(tuple(sorted(quantize(point) for point in face)) for face in raw_faces)
    return vertices, edges, faces


def compare_selected_islands(obj, tolerance):
    """Return ``(status, message)`` for the current UV selection."""
    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        return "ERROR", "The active mesh has no UV map."

    islands = selected_uv_islands(bm, uv_layer, tolerance)
    if len(islands) != 2:
        return "ERROR", f"Select exactly two complete UV islands (found {len(islands)})."

    island_a, island_b = islands
    if len(island_a) != len(island_b):
        return "NO_MATCH", f"Different face counts: {len(island_a)} vs {len(island_b)}."

    signature_a = island_signature(island_a, uv_layer, TRANSFORMS[0][1], tolerance)
    for label, transform in TRANSFORMS:
        signature_b = island_signature(island_b, uv_layer, transform, tolerance)
        if signature_a == signature_b:
            return "MATCH", f"Exact match: {label}."

    return "NO_MATCH", "Not an exact match."


def store_result(context, status, message):
    wm = context.window_manager
    wm.rizum_uv_compare_last_status = status
    wm.rizum_uv_compare_last_result = message


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
        if context.scene.tool_settings.use_uv_select_sync:
            message = "Turn off UV Sync Selection before comparing."
            store_result(context, "ERROR", message)
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        tolerance = context.window_manager.rizum_uv_compare_tolerance
        status, message = compare_selected_islands(context.edit_object, tolerance)
        store_result(context, status, message)

        report_level = {"MATCH": {"INFO"}, "NO_MATCH": {"WARNING"}, "ERROR": {"ERROR"}}
        self.report(report_level[status], message)
        print(f"Rizum UV Compare: {message} (tolerance {tolerance:g})")
        return {"CANCELLED"} if status == "ERROR" else {"FINISHED"}


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
        sync_enabled = context.scene.tool_settings.use_uv_select_sync

        layout.label(text="Select two complete UV islands.", icon="UV")

        if sync_enabled:
            warning = layout.box()
            warning.alert = True
            warning.label(text="UV Sync Selection is on.", icon="ERROR")
            warning.label(text="Turn it off before comparing.")

        settings = layout.box()
        settings.prop(wm, "rizum_uv_compare_tolerance", text="Tolerance")

        action = layout.column()
        action.enabled = not sync_enabled
        action.scale_y = 1.25
        action.operator("uv.rizum_compare_islands", icon="VIEWZOOM")

        result_box = layout.box()
        status_icons = {
            "NONE": "QUESTION",
            "MATCH": "CHECKMARK",
            "NO_MATCH": "X",
            "ERROR": "ERROR",
        }
        result_box.label(text="Last Result", icon=status_icons[wm.rizum_uv_compare_last_status])
        for line in textwrap.wrap(wm.rizum_uv_compare_last_result, width=38):
            result_box.label(text=line)


CLASSES = (
    UV_OT_rizum_compare_islands,
    UV_PT_rizum_compare,
)


def register():
    bpy.types.WindowManager.rizum_uv_compare_tolerance = FloatProperty(
        name="Tolerance",
        description="Maximum UV-coordinate difference counted as equal",
        default=DEFAULT_TOLERANCE,
        min=1.0e-8,
        max=1.0e-2,
        precision=6,
    )
    bpy.types.WindowManager.rizum_uv_compare_last_result = StringProperty(
        name="Last Result",
        default="No comparison yet.",
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
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.rizum_uv_compare_last_status
    del bpy.types.WindowManager.rizum_uv_compare_last_result
    del bpy.types.WindowManager.rizum_uv_compare_tolerance


if __name__ == "__main__":
    register()
