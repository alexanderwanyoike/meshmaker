import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import AddonPreferences


class CharMakerPreferences(AddonPreferences):
    bl_idname = __package__

    runpod_api_key: StringProperty(
        name="RunPod API Key",
        description="Your RunPod API key",
        subtype='PASSWORD',
    )

    trellis_endpoint_id: StringProperty(
        name="Trellis Endpoint ID",
        description="RunPod endpoint ID for Trellis 2",
    )

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

        layout.label(text="RunPod / Trellis 2:", icon='MESH_MONKEY')
        layout.prop(self, "runpod_api_key")
        layout.prop(self, "trellis_endpoint_id")

        layout.separator()
        layout.label(text="Gemini Image Generation:", icon='IMAGE_DATA')
        layout.prop(self, "gemini_api_key")
        layout.prop(self, "gemini_model")


def register():
    bpy.utils.register_class(CharMakerPreferences)


def unregister():
    bpy.utils.unregister_class(CharMakerPreferences)
