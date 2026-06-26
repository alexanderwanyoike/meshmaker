"""Blender UI panels for MeshMaker mesh generation."""

import bpy
from bpy.types import Panel

from .. import ADDON_ID
from .operators import MESH_MODELS, PREVIEW_NAME


class MESHMAKER_PT_main(Panel):
    bl_label = "MeshMaker"
    bl_idname = "MESHMAKER_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "MeshMaker"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        prefs = context.preferences.addons.get(ADDON_ID)
        if prefs is None:
            layout.label(text="Addon not found", icon='ERROR')
            return
        prefs = prefs.preferences

        model_key = wm.meshmaker_model_backend
        model = MESH_MODELS[model_key]

        missing_provider = not getattr(prefs, model["api_key_field"], "")
        missing_gemini = not prefs.gemini_api_key

        if missing_provider or missing_gemini:
            if missing_gemini:
                layout.label(text="Set Gemini key in preferences", icon='INFO')
            if missing_provider:
                layout.label(text=f"Set {model['label']} API key", icon='INFO')
            layout.operator(
                "preferences.addon_show",
                text="Open Preferences",
                icon='PREFERENCES',
            ).module = ADDON_ID
            layout.separator()

        # Provider selector
        layout.prop(wm, "meshmaker_model_backend", text="Provider")

        # Workflow toggle
        row = layout.row(align=True)
        row.prop(wm, "meshmaker_workflow", expand=True)

        layout.separator()

        busy = wm.meshmaker_status.startswith("Generating")

        if wm.meshmaker_workflow == 'GENERATE':
            self._draw_generate_workflow(layout, wm, busy)
        else:
            self._draw_file_workflow(layout, wm, busy)

        # Status (shared)
        layout.separator()
        status = wm.meshmaker_status
        if status.startswith("Error"):
            layout.label(text=status, icon='ERROR')
        elif status.startswith("Done"):
            layout.label(text=status, icon='CHECKMARK')
        elif status.startswith("Image ready"):
            layout.label(text=status, icon='CHECKMARK')
        elif status.startswith("Generating"):
            layout.label(text=status, icon='SORTTIME')
        else:
            layout.label(text=status, icon='INFO')

    def _draw_settings(self, layout, wm):
        layout.label(text="3D Settings:")
        layout.prop(wm, "meshmaker_face_count", text="Face Count")
        layout.prop(wm, "meshmaker_enable_pbr", text="PBR Materials")

    def _draw_generate_workflow(self, layout, wm, busy):
        preview = bpy.data.images.get(PREVIEW_NAME)
        has_preview = preview is not None

        # Prompt
        col = layout.column(align=True)
        col.label(text="Prompt:")
        col.prop(wm, "meshmaker_prompt", text="")

        # Generate / Edit button
        row = col.row(align=True)
        row.scale_y = 1.5
        row.enabled = not busy
        if has_preview:
            row.operator("meshmaker.generate_image", text="Edit Image", icon='BRUSH_DATA')
        else:
            row.operator("meshmaker.generate_image", text="Generate Image", icon='IMAGE_DATA')

        # Preview display
        if has_preview:
            layout.separator()
            if preview.preview and preview.preview.icon_id:
                layout.template_icon(icon_value=preview.preview.icon_id, scale=10.0)
            else:
                layout.label(text="(preview loading...)")

            layout.operator("meshmaker.clear_preview", text="Clear", icon='X')

            # 3D settings + generate
            layout.separator()
            col = layout.column(align=True)
            self._draw_settings(col, wm)

            layout.separator()
            row = layout.row(align=True)
            row.scale_y = 1.5
            row.enabled = not busy

            op = row.operator(
                "meshmaker.generate_mesh",
                text="Generating mesh..." if busy else "Generate 3D",
                icon='MESH_MONKEY',
            )
            op.image_path = ""  # Will fall back to preview
            op.face_count = wm.meshmaker_face_count
            op.enable_pbr = wm.meshmaker_enable_pbr

    def _draw_file_workflow(self, layout, wm, busy):
        col = layout.column(align=True)
        col.label(text="Reference Image:")
        col.prop(wm, "meshmaker_image_path", text="")

        col.separator()
        self._draw_settings(col, wm)

        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.enabled = not busy

        op = row.operator(
            "meshmaker.generate_mesh",
            text="Generating mesh..." if busy else "Generate 3D",
            icon='MESH_MONKEY',
        )
        op.image_path = wm.meshmaker_image_path
        op.face_count = wm.meshmaker_face_count
        op.enable_pbr = wm.meshmaker_enable_pbr


def register():
    bpy.utils.register_class(MESHMAKER_PT_main)

    wm = bpy.types.WindowManager
    wm.meshmaker_workflow = bpy.props.EnumProperty(
        name="Workflow",
        items=[
            ('GENERATE', "Generate Image", "Text prompt → Gemini image → 3D"),
            ('FILE', "Use File", "Image file → 3D"),
        ],
        default='GENERATE',
    )
    wm.meshmaker_image_path = bpy.props.StringProperty(
        name="Image Path",
        description="Path to the reference image",
        subtype='FILE_PATH',
    )
    wm.meshmaker_face_count = bpy.props.IntProperty(
        name="Face Count",
        description="Target polygon count for the generated mesh",
        default=50000,
        min=40000,
        max=500000,
    )
    wm.meshmaker_enable_pbr = bpy.props.BoolProperty(
        name="PBR Materials",
        description="Request PBR material maps (may cost extra)",
        default=False,
    )


def unregister():
    wm = bpy.types.WindowManager
    del wm.meshmaker_enable_pbr
    del wm.meshmaker_face_count
    del wm.meshmaker_image_path
    del wm.meshmaker_workflow

    bpy.utils.unregister_class(MESHMAKER_PT_main)
