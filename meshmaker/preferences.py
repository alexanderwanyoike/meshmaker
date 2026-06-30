import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import AddonPreferences

from . import ADDON_ID


class MeshMakerPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    # --- Generate providers (bring your own key) ---
    fal_api_key: StringProperty(
        name="Fal API Key",
        description="API key for Fal (Hunyuan3D, Pixal3D, Tripo, Rodin)",
        subtype='PASSWORD',
    )

    meshy_api_key: StringProperty(
        name="Meshy API Key",
        description="API key for Meshy image-to-3D",
        subtype='PASSWORD',
    )

    # --- Gemini (concept image generation) ---
    gemini_api_key: StringProperty(
        name="Gemini API Key",
        description="Google Gemini API key for image generation",
        subtype='PASSWORD',
    )

    gemini_model: EnumProperty(
        name="Gemini Model",
        items=[
            ('gemini-2.5-flash-image',
             "2.5 Flash",
             "Fast image generation (default)"),
            ('gemini-3-pro-image-preview',
             "3 Pro (Preview)",
             "Highest quality, reasoning-enhanced"),
        ],
        default='gemini-2.5-flash-image',
    )

    def draw(self, context):
        layout = self.layout

        layout.label(text="Generate Providers (bring your own key):", icon='URL')
        layout.prop(self, "fal_api_key")
        layout.prop(self, "meshy_api_key")

        layout.separator()
        layout.label(text="Gemini Image Generation:", icon='IMAGE_DATA')
        layout.prop(self, "gemini_api_key")
        layout.prop(self, "gemini_model")


def register():
    bpy.utils.register_class(MeshMakerPreferences)


def unregister():
    bpy.utils.unregister_class(MeshMakerPreferences)
