import bpy
from bpy.props import StringProperty
from bpy.types import AddonPreferences


class RigMakerPreferences(AddonPreferences):
    bl_idname = __package__

    runpod_api_key: StringProperty(
        name="RunPod API Key",
        description="Your RunPod API key",
        subtype='PASSWORD',
    )

    mia_endpoint_id: StringProperty(
        name="MIA Endpoint ID",
        description="RunPod endpoint ID for Make It Animatable",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="RunPod / Make It Animatable:", icon='ARMATURE_DATA')
        layout.prop(self, "runpod_api_key")
        layout.prop(self, "mia_endpoint_id")


def register():
    bpy.utils.register_class(RigMakerPreferences)


def unregister():
    bpy.utils.unregister_class(RigMakerPreferences)
