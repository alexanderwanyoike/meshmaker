import bpy
from bpy.props import StringProperty
from bpy.types import AddonPreferences


class AnimMakerPreferences(AddonPreferences):
    bl_idname = __package__

    runpod_api_key: StringProperty(
        name="RunPod API Key",
        description="Your RunPod API key",
        subtype='PASSWORD',
    )

    hymotion_endpoint_id: StringProperty(
        name="HY-Motion Endpoint ID",
        description="RunPod endpoint ID for HY-Motion",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="RunPod / HY-Motion:", icon='ANIM')
        layout.prop(self, "runpod_api_key")
        layout.prop(self, "hymotion_endpoint_id")


def register():
    bpy.utils.register_class(AnimMakerPreferences)


def unregister():
    bpy.utils.unregister_class(AnimMakerPreferences)
