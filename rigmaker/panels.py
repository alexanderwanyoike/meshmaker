"""Blender UI panels for RigMaker."""

import bpy
from bpy.types import Panel


class RIGMAKER_PT_main(Panel):
    bl_label = "RigMaker"
    bl_idname = "RIGMAKER_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "RigMaker"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # Check for preferences
        prefs = context.preferences.addons.get(__package__)
        if prefs is None:
            layout.label(text="Addon not found", icon='ERROR')
            return
        prefs = prefs.preferences

        missing = not prefs.runpod_api_key or not prefs.unirig_endpoint_id

        if missing:
            layout.label(text="Set RunPod key & endpoint in preferences", icon='INFO')
            layout.operator(
                "preferences.addon_show",
                text="Open Preferences",
                icon='PREFERENCES',
            ).module = __package__
            layout.separator()

        busy = wm.rigmaker_status.startswith("Rigging")

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

        # Seed
        layout.separator()
        layout.prop(wm, "rigmaker_seed", text="Seed")

        # Rig button
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.enabled = not busy and not missing and obj is not None and obj.type == 'MESH'
        row.operator(
            "rigmaker.auto_rig",
            text="Rigging mesh..." if busy else "Rig",
            icon='ARMATURE_DATA',
        )

        # Status
        layout.separator()
        status = wm.rigmaker_status
        if status.startswith("Error"):
            layout.label(text=status, icon='ERROR')
        elif status.startswith("Done"):
            layout.label(text=status, icon='CHECKMARK')
        elif status.startswith("Rigging"):
            layout.label(text=status, icon='SORTTIME')
        else:
            layout.label(text=status, icon='INFO')


def register():
    bpy.utils.register_class(RIGMAKER_PT_main)


def unregister():
    bpy.utils.unregister_class(RIGMAKER_PT_main)
