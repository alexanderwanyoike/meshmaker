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

    unirig_endpoint_id: StringProperty(
        name="UniRig Endpoint ID",
        description="RunPod endpoint ID for UniRig",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="RunPod / UniRig:", icon='ARMATURE_DATA')
        layout.prop(self, "runpod_api_key")
        layout.prop(self, "unirig_endpoint_id")


def register():
    bpy.utils.register_class(RigMakerPreferences)


def unregister():
    bpy.utils.unregister_class(RigMakerPreferences)
