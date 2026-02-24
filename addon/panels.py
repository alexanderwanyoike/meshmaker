"""Blender UI panels for CharMaker."""

import bpy
from bpy.types import Panel

from .operators import PREVIEW_NAME


class CHARMAKER_PT_main(Panel):
    bl_label = "CharMaker"
    bl_idname = "CHARMAKER_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CharMaker"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        # Check for preferences
        prefs = context.preferences.addons.get(__package__)
        if prefs is None:
            layout.label(text="Addon not found", icon='ERROR')
            return
        prefs = prefs.preferences

        missing_runpod = not prefs.runpod_api_key or not prefs.trellis_endpoint_id
        missing_gemini = not prefs.gemini_api_key

        if missing_runpod or missing_gemini:
            if missing_gemini:
                layout.label(text="Set Gemini key in preferences", icon='INFO')
            if missing_runpod:
                layout.label(text="Set RunPod key & endpoint in preferences", icon='INFO')
            layout.operator(
                "preferences.addon_show",
                text="Open Preferences",
                icon='PREFERENCES',
            ).module = __package__
            layout.separator()

        # Workflow toggle
        row = layout.row(align=True)
        row.prop(wm, "charmaker_workflow", expand=True)

        layout.separator()

        busy = wm.charmaker_status.startswith("Generating")

        if wm.charmaker_workflow == 'GENERATE':
            self._draw_generate_workflow(layout, wm, busy)
        else:
            self._draw_file_workflow(layout, wm, busy)

        # Status (shared)
        layout.separator()
        status = wm.charmaker_status
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

    def _draw_generate_workflow(self, layout, wm, busy):
        preview = bpy.data.images.get(PREVIEW_NAME)
        has_preview = preview is not None

        # Prompt
        col = layout.column(align=True)
        col.label(text="Prompt:")
        col.prop(wm, "charmaker_prompt", text="")

        # Generate / Edit button
        row = col.row(align=True)
        row.scale_y = 1.5
        row.enabled = not busy
        if has_preview:
            row.operator("charmaker.generate_image", text="Edit Image", icon='BRUSH_DATA')
        else:
            row.operator("charmaker.generate_image", text="Generate Image", icon='IMAGE_DATA')

        # Preview display
        if has_preview:
            layout.separator()
            if preview.preview and preview.preview.icon_id:
                layout.template_icon(icon_value=preview.preview.icon_id, scale=10.0)
            else:
                layout.label(text="(preview loading...)")

            layout.operator("charmaker.clear_preview", text="Clear", icon='X')

            # Trellis settings + generate 3D
            layout.separator()
            col = layout.column(align=True)
            col.label(text="3D Settings:")
            col.prop(wm, "charmaker_resolution", text="Resolution")
            col.prop(wm, "charmaker_texture_size", text="Texture Size")
            col.prop(wm, "charmaker_seed", text="Seed")

            layout.separator()
            row = layout.row(align=True)
            row.scale_y = 1.5
            row.enabled = not busy

            op = row.operator(
                "charmaker.generate_mesh",
                text="Generating mesh..." if busy else "Generate 3D",
                icon='MESH_MONKEY',
            )
            op.image_path = ""  # Will fall back to preview
            op.resolution = wm.charmaker_resolution
            op.texture_size = wm.charmaker_texture_size
            op.seed = wm.charmaker_seed

    def _draw_file_workflow(self, layout, wm, busy):
        col = layout.column(align=True)
        col.label(text="Reference Image:")
        col.prop(wm, "charmaker_image_path", text="")

        col.separator()
        col.label(text="Settings:")
        col.prop(wm, "charmaker_resolution", text="Resolution")
        col.prop(wm, "charmaker_texture_size", text="Texture Size")
        col.prop(wm, "charmaker_seed", text="Seed")

        # Generate button
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 1.5
        row.enabled = not busy

        op = row.operator(
            "charmaker.generate_mesh",
            text="Generating mesh..." if busy else "Generate 3D",
            icon='MESH_MONKEY',
        )
        op.image_path = wm.charmaker_image_path
        op.resolution = wm.charmaker_resolution
        op.texture_size = wm.charmaker_texture_size
        op.seed = wm.charmaker_seed


def register():
    bpy.utils.register_class(CHARMAKER_PT_main)

    wm = bpy.types.WindowManager
    wm.charmaker_workflow = bpy.props.EnumProperty(
        name="Workflow",
        items=[
            ('GENERATE', "Generate Image", "Text prompt → Gemini image → 3D"),
            ('FILE', "Use File", "Image file → 3D"),
        ],
        default='GENERATE',
    )
    wm.charmaker_image_path = bpy.props.StringProperty(
        name="Image Path",
        description="Path to the reference image",
        subtype='FILE_PATH',
    )
    wm.charmaker_resolution = bpy.props.EnumProperty(
        name="Resolution",
        items=[
            ('512', "512", "Fast, lower quality"),
            ('1024', "1024", "Balanced"),
            ('1536', "1536", "Slow, higher quality"),
        ],
        default='512',
    )
    wm.charmaker_texture_size = bpy.props.EnumProperty(
        name="Texture Size",
        items=[
            ('1024', "1024", "Smaller file size"),
            ('2048', "2048", "Balanced (default)"),
            ('4096', "4096", "High quality textures"),
        ],
        default='2048',
    )
    wm.charmaker_seed = bpy.props.IntProperty(
        name="Seed",
        description="Random seed (0 = random)",
        default=0,
        min=0,
    )


def unregister():
    wm = bpy.types.WindowManager
    del wm.charmaker_seed
    del wm.charmaker_texture_size
    del wm.charmaker_resolution
    del wm.charmaker_image_path
    del wm.charmaker_workflow

    bpy.utils.unregister_class(CHARMAKER_PT_main)
