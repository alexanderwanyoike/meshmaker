"""
Generate bones_vroid.fbx for MIA's dataset_mixamo_additional.py.

The additional dataset extends standard Mixamo with 7 extra bones
(rabbit ears + fox tail). ADDITIONAL_BONES=False in init_models() so
this skeleton is never used for inference — we only need to pass the
import-time assertion: len(KINEMATIC_TREE) == len(MIXAMO_JOINTS) == 59.
"""
import os
import bpy

OUTPUT_PATH = "/app/mia/data/Mixamo/bones_vroid.fbx"

# Standard 52 Mixamo bones + 7 additional = 59 total
# Must exactly match MIXAMO_JOINTS in dataset_mixamo_additional.py
VROID_HIERARCHY = [
    # Standard Mixamo (52)
    ("mixamorig:Hips", None),
    ("mixamorig:Spine", "mixamorig:Hips"),
    ("mixamorig:Spine1", "mixamorig:Spine"),
    ("mixamorig:Spine2", "mixamorig:Spine1"),
    ("mixamorig:Neck", "mixamorig:Spine2"),
    ("mixamorig:Head", "mixamorig:Neck"),
    ("mixamorig:LeftShoulder", "mixamorig:Spine2"),
    ("mixamorig:LeftArm", "mixamorig:LeftShoulder"),
    ("mixamorig:LeftForeArm", "mixamorig:LeftArm"),
    ("mixamorig:LeftHand", "mixamorig:LeftForeArm"),
    ("mixamorig:LeftHandThumb1", "mixamorig:LeftHand"),
    ("mixamorig:LeftHandThumb2", "mixamorig:LeftHandThumb1"),
    ("mixamorig:LeftHandThumb3", "mixamorig:LeftHandThumb2"),
    ("mixamorig:LeftHandIndex1", "mixamorig:LeftHand"),
    ("mixamorig:LeftHandIndex2", "mixamorig:LeftHandIndex1"),
    ("mixamorig:LeftHandIndex3", "mixamorig:LeftHandIndex2"),
    ("mixamorig:LeftHandMiddle1", "mixamorig:LeftHand"),
    ("mixamorig:LeftHandMiddle2", "mixamorig:LeftHandMiddle1"),
    ("mixamorig:LeftHandMiddle3", "mixamorig:LeftHandMiddle2"),
    ("mixamorig:LeftHandRing1", "mixamorig:LeftHand"),
    ("mixamorig:LeftHandRing2", "mixamorig:LeftHandRing1"),
    ("mixamorig:LeftHandRing3", "mixamorig:LeftHandRing2"),
    ("mixamorig:LeftHandPinky1", "mixamorig:LeftHand"),
    ("mixamorig:LeftHandPinky2", "mixamorig:LeftHandPinky1"),
    ("mixamorig:LeftHandPinky3", "mixamorig:LeftHandPinky2"),
    ("mixamorig:RightShoulder", "mixamorig:Spine2"),
    ("mixamorig:RightArm", "mixamorig:RightShoulder"),
    ("mixamorig:RightForeArm", "mixamorig:RightArm"),
    ("mixamorig:RightHand", "mixamorig:RightForeArm"),
    ("mixamorig:RightHandThumb1", "mixamorig:RightHand"),
    ("mixamorig:RightHandThumb2", "mixamorig:RightHandThumb1"),
    ("mixamorig:RightHandThumb3", "mixamorig:RightHandThumb2"),
    ("mixamorig:RightHandIndex1", "mixamorig:RightHand"),
    ("mixamorig:RightHandIndex2", "mixamorig:RightHandIndex1"),
    ("mixamorig:RightHandIndex3", "mixamorig:RightHandIndex2"),
    ("mixamorig:RightHandMiddle1", "mixamorig:RightHand"),
    ("mixamorig:RightHandMiddle2", "mixamorig:RightHandMiddle1"),
    ("mixamorig:RightHandMiddle3", "mixamorig:RightHandMiddle2"),
    ("mixamorig:RightHandRing1", "mixamorig:RightHand"),
    ("mixamorig:RightHandRing2", "mixamorig:RightHandRing1"),
    ("mixamorig:RightHandRing3", "mixamorig:RightHandRing2"),
    ("mixamorig:RightHandPinky1", "mixamorig:RightHand"),
    ("mixamorig:RightHandPinky2", "mixamorig:RightHandPinky1"),
    ("mixamorig:RightHandPinky3", "mixamorig:RightHandPinky2"),
    ("mixamorig:LeftUpLeg", "mixamorig:Hips"),
    ("mixamorig:LeftLeg", "mixamorig:LeftUpLeg"),
    ("mixamorig:LeftFoot", "mixamorig:LeftLeg"),
    ("mixamorig:LeftToeBase", "mixamorig:LeftFoot"),
    ("mixamorig:RightUpLeg", "mixamorig:Hips"),
    ("mixamorig:RightLeg", "mixamorig:RightUpLeg"),
    ("mixamorig:RightFoot", "mixamorig:RightLeg"),
    ("mixamorig:RightToeBase", "mixamorig:RightFoot"),
    # Additional VRoid bones (7) — from ADDITIONAL_JOINTS in dataset_mixamo_additional.py
    ("mixamorig:LRabbitEar2", "mixamorig:Head"),
    ("mixamorig:RRabbitEar2", "mixamorig:Head"),
    ("mixamorig:FoxTail1", "mixamorig:Hips"),
    ("mixamorig:FoxTail2", "mixamorig:FoxTail1"),
    ("mixamorig:FoxTail3", "mixamorig:FoxTail2"),
    ("mixamorig:FoxTail4", "mixamorig:FoxTail3"),
    ("mixamorig:FoxTail5", "mixamorig:FoxTail4"),
]

assert len(VROID_HIERARCHY) == 59

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

arm_data = bpy.data.armatures.new("Armature")
arm_obj = bpy.data.objects.new("Armature", arm_data)
bpy.context.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
arm_obj.select_set(True)

bpy.ops.object.mode_set(mode='EDIT')

for i, (name, parent_name) in enumerate(VROID_HIERARCHY):
    bone = arm_data.edit_bones.new(name)
    bone.head = (0.0, 0.0, i * 0.1)
    bone.tail = (0.0, 0.0, i * 0.1 + 0.05)
    if parent_name:
        bone.parent = arm_data.edit_bones[parent_name]

bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.export_scene.fbx(
    filepath=OUTPUT_PATH,
    use_selection=False,
    object_types={'ARMATURE'},
    add_leaf_bones=False,
)

print(f"Created {OUTPUT_PATH} with {len(VROID_HIERARCHY)} bones")
