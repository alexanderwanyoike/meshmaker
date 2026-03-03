import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import AddonPreferences

from . import ADDON_ID


class MeshMakerPreferences(AddonPreferences):
    bl_idname = ADDON_ID

    # --- Shared ---
    runpod_api_key: StringProperty(
        name="RunPod API Key",
        description="Your RunPod API key",
        subtype='PASSWORD',
    )

    # --- Mesh generation ---
    trellis_endpoint_id: StringProperty(
        name="Trellis 2 Endpoint ID",
        description="RunPod endpoint ID for Trellis 2",
    )

    hunyuan3d_endpoint_id: StringProperty(
        name="Hunyuan3D 2.1 Endpoint ID",
        description="RunPod endpoint ID for Hunyuan3D 2.1",
    )

    # --- Rigging ---
    mia_endpoint_id: StringProperty(
        name="MIA Endpoint ID",
        description="RunPod endpoint ID for Make It Animatable",
    )

    # --- Animation ---
    hymotion_endpoint_id: StringProperty(
        name="HY-Motion Endpoint ID",
        description="RunPod endpoint ID for HY-Motion",
    )

    # --- Segmentation ---
    segment_endpoint_id: StringProperty(
        name="Hunyuan3D-Part Endpoint ID",
        description="RunPod endpoint ID for P3-SAM part segmentation",
    )

    # --- Gemini ---
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

        layout.label(text="RunPod (shared):", icon='URL')
        layout.prop(self, "runpod_api_key")

        layout.separator()
        layout.label(text="Mesh Generation:", icon='MESH_MONKEY')
        layout.prop(self, "trellis_endpoint_id")
        layout.prop(self, "hunyuan3d_endpoint_id")

        layout.separator()
        layout.label(text="Rigging:", icon='ARMATURE_DATA')
        layout.prop(self, "mia_endpoint_id")

        layout.separator()
        layout.label(text="Animation:", icon='ANIM')
        layout.prop(self, "hymotion_endpoint_id")

        layout.separator()
        layout.label(text="Part Segmentation:", icon='MESH_DATA')
        layout.prop(self, "segment_endpoint_id")

        layout.separator()
        layout.label(text="Gemini Image Generation:", icon='IMAGE_DATA')
        layout.prop(self, "gemini_api_key")
        layout.prop(self, "gemini_model")


def register():
    bpy.utils.register_class(MeshMakerPreferences)


def unregister():
    bpy.utils.unregister_class(MeshMakerPreferences)
