"""Blender UI panels for AnimMaker."""

import bpy
from bpy.types import Panel

from .. import ADDON_ID


class ANIMMAKER_PT_main(Panel):
    bl_label = "AnimMaker"
    bl_idname = "ANIMMAKER_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AnimMaker"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # Check for preferences
        prefs = context.preferences.addons.get(ADDON_ID)
        if prefs is None:
            layout.label(text="Addon not found", icon='ERROR')
            return
        prefs = prefs.preferences

        missing = not prefs.runpod_api_key or not prefs.hymotion_endpoint_id

        if missing:
            layout.label(text="Set RunPod key & endpoint in preferences", icon='INFO')
            layout.operator(
                "preferences.addon_show",
                text="Open Preferences",
                icon='PREFERENCES',
            ).module = ADDON_ID
            layout.separator()

        busy = wm.animmaker_status.startswith("Generating")

        # Selected armature info
        obj = context.active_object
        is_armature = obj is not None and obj.type == 'ARMATURE'
        is_mixamo = is_armature and "mixamorig:Hips" in obj.data.bones

        if is_mixamo:
            box = layout.box()
            box.label(text=obj.name, icon='ARMATURE_DATA')
            box.label(text=f"Bones: {len(obj.data.bones)}")
        elif is_armature:
            layout.label(text="Not a Mixamo armature (no mixamorig:Hips)", icon='ERROR')
        else:
            layout.label(text="No armature selected", icon='ERROR')

        # Prompt
        layout.separator()
        layout.prop(wm, "animmaker_prompt", text="", icon='TEXT')

        # Settings
        layout.separator()
        col = layout.column(align=True)
        col.prop(wm, "animmaker_duration")
        col.prop(wm, "animmaker_fps")
        col.prop(wm, "animmaker_seed")
        col.prop(wm, "animmaker_guidance")

        # Animate button
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        has_prompt = bool(wm.animmaker_prompt.strip())
        row.enabled = not busy and not missing and is_mixamo and has_prompt
        row.operator(
            "animmaker.animate",
            text="Generating..." if busy else "Animate",
            icon='ANIM',
        )

        # Status
        layout.separator()
        status = wm.animmaker_status
        if status.startswith("Error"):
            layout.label(text=status, icon='ERROR')
        elif status.startswith("Done"):
            layout.label(text=status, icon='CHECKMARK')
        elif status.startswith("Generating"):
            layout.label(text=status, icon='SORTTIME')
        else:
            layout.label(text=status, icon='INFO')


def register():
    bpy.utils.register_class(ANIMMAKER_PT_main)


def unregister():
    bpy.utils.unregister_class(ANIMMAKER_PT_main)
