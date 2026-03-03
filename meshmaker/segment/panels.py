"""Blender UI panels for PartMaker segmentation."""

import bpy
from bpy.types import Panel

from .. import ADDON_ID


class SEGMENT_PT_main(Panel):
    bl_label = "PartMaker"
    bl_idname = "SEGMENT_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PartMaker"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # Check for preferences
        prefs = context.preferences.addons.get(ADDON_ID)
        if prefs is None:
            layout.label(text="Addon not found", icon='ERROR')
            return
        prefs = prefs.preferences

        missing = not prefs.runpod_api_key or not prefs.segment_endpoint_id

        if missing:
            layout.label(text="Set RunPod key & endpoint in preferences", icon='INFO')
            layout.operator(
                "preferences.addon_show",
                text="Open Preferences",
                icon='PREFERENCES',
            ).module = ADDON_ID
            layout.separator()

        busy = wm.segment_status.startswith("Segmenting")

        # Selected object info
        obj = context.active_object
        if obj is not None and obj.type == 'MESH':
            box = layout.box()
            box.label(text=obj.name, icon='OUTLINER_OB_MESH')
            mesh = obj.data
            row = box.row()
            row.label(text=f"Verts: {len(mesh.vertices):,}")
            row.label(text=f"Faces: {len(mesh.polygons):,}")
        else:
            layout.label(text="No mesh selected", icon='ERROR')

        # Segment button
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.enabled = not busy and not missing and obj is not None and obj.type == 'MESH'
        row.operator(
            "segment.segment_mesh",
            text="Segmenting..." if busy else "Segment Parts",
            icon='MESH_DATA',
        )

        # Status
        layout.separator()
        status = wm.segment_status
        if status.startswith("Error"):
            layout.label(text=status, icon='ERROR')
        elif status.startswith("Done"):
            layout.label(text=status, icon='CHECKMARK')
        elif status.startswith("Segmenting"):
            layout.label(text=status, icon='SORTTIME')
        else:
            layout.label(text=status, icon='INFO')


def register():
    bpy.utils.register_class(SEGMENT_PT_main)


def unregister():
    bpy.utils.unregister_class(SEGMENT_PT_main)
