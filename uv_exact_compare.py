# SPDX-License-Identifier: GPL-3.0-or-later

"""
UV Exact Compare — Blender 4.2 / 5.x

Usage:
1. Enter Edit Mode on one mesh and make the relevant faces visible.
2. In the UV Editor, turn UV Sync Selection off.
3. Select exactly two complete UV islands.
4. Open this file in Blender's Text Editor and press Alt+P / Run Script.

The comparison ignores translation, but not scale or deformation. It tests the
same orientation, X/Y mirrors, 90/180-degree rotations, and diagonal mirrors.
"""

__version__ = "0.1.0"

import bpy
import bmesh
from collections import Counter, defaultdict, deque

TOLERANCE = 1.0e-5


def uv_selected(loop, uv_layer):
    if hasattr(loop, "uv_select_vert"):
        return loop.uv_select_vert
    return loop[uv_layer].select


def close_uv(a, b, tolerance):
    return abs(a.x - b.x) <= tolerance and abs(a.y - b.y) <= tolerance


def selected_uv_islands(bm, uv_layer, tolerance):
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
        if len(shared) == 2 and all(close_uv(map_a[v], map_b[v], tolerance) for v in shared):
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


TRANSFORMS = (
    ("same orientation", lambda x, y: (x, y)),
    ("mirrored horizontally (X)", lambda x, y: (-x, y)),
    ("mirrored vertically (Y)", lambda x, y: (x, -y)),
    ("rotated 180°", lambda x, y: (-x, -y)),
    ("rotated 90° counter-clockwise", lambda x, y: (-y, x)),
    ("rotated 90° clockwise", lambda x, y: (y, -x)),
    ("mirrored across the X=Y diagonal", lambda x, y: (y, x)),
    ("mirrored across the X=-Y diagonal", lambda x, y: (-y, -x)),
)


def island_signature(island, uv_layer, transform, tolerance):
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


def popup(message, icon="INFO"):
    def draw(self, _context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title="UV Exact Compare", icon=icon)


def main():
    obj = bpy.context.edit_object
    if obj is None or obj.type != "MESH":
        popup("Enter Mesh Edit Mode first.", "ERROR")
        return

    bm = bmesh.from_edit_mesh(obj.data)
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        popup("The active mesh has no UV map.", "ERROR")
        return

    islands = selected_uv_islands(bm, uv_layer, TOLERANCE)
    if len(islands) != 2:
        popup(f"Select exactly two complete UV islands (found {len(islands)}).", "ERROR")
        return

    island_a, island_b = islands
    if len(island_a) != len(island_b):
        popup(f"Not identical: {len(island_a)} vs {len(island_b)} faces.", "ERROR")
        return

    signature_a = island_signature(island_a, uv_layer, TRANSFORMS[0][1], TOLERANCE)
    for label, transform in TRANSFORMS:
        signature_b = island_signature(island_b, uv_layer, transform, TOLERANCE)
        if signature_a == signature_b:
            result = f"Exact match: {label} (tolerance {TOLERANCE:g})"
            print("UV Exact Compare:", result)
            popup(result, "CHECKMARK")
            return

    result = f"Not an exact match (tolerance {TOLERANCE:g})"
    print("UV Exact Compare:", result)
    popup(result, "ERROR")


main()
