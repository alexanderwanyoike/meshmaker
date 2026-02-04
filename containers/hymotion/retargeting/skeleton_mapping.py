"""
SMPL-H to Mixamo skeleton joint mapping.

SMPL-H has 22 body joints that need to be mapped to Mixamo bone names.
Mixamo bones can be either prefixed with "mixamorig:" or unprefixed.
"""

# SMPL-H joint names in order (indices 0-21)
SMPLH_JOINT_NAMES = [
    "pelvis",       # 0
    "left_hip",     # 1
    "right_hip",    # 2
    "spine1",       # 3
    "left_knee",    # 4
    "right_knee",   # 5
    "spine2",       # 6
    "left_ankle",   # 7
    "right_ankle",  # 8
    "spine3",       # 9
    "left_foot",    # 10
    "right_foot",   # 11
    "neck",         # 12
    "left_collar",  # 13
    "right_collar", # 14
    "head",         # 15
    "left_shoulder",  # 16
    "right_shoulder", # 17
    "left_elbow",   # 18
    "right_elbow",  # 19
    "left_wrist",   # 20
    "right_wrist",  # 21
]

# Mapping from SMPL-H joint name to Mixamo bone name (without prefix)
SMPLH_TO_MIXAMO = {
    "pelvis": "Hips",
    "left_hip": "LeftUpLeg",
    "right_hip": "RightUpLeg",
    "spine1": "Spine",
    "spine2": "Spine1",
    "spine3": "Spine2",
    "left_knee": "LeftLeg",
    "right_knee": "RightLeg",
    "left_ankle": "LeftFoot",
    "right_ankle": "RightFoot",
    "left_foot": "LeftToeBase",
    "right_foot": "RightToeBase",
    "neck": "Neck",
    "head": "Head",
    "left_collar": "LeftShoulder",
    "right_collar": "RightShoulder",
    "left_shoulder": "LeftArm",
    "right_shoulder": "RightArm",
    "left_elbow": "LeftForeArm",
    "right_elbow": "RightForeArm",
    "left_wrist": "LeftHand",
    "right_wrist": "RightHand",
}

# Core Mixamo bones that must be present for a valid rig
MIXAMO_REQUIRED_BONES = [
    "Hips",
    "Spine",
    "LeftUpLeg",
    "RightUpLeg",
    "LeftLeg",
    "RightLeg",
    "LeftFoot",
    "RightFoot",
    "LeftArm",
    "RightArm",
    "LeftForeArm",
    "RightForeArm",
    "LeftHand",
    "RightHand",
    "Head",
]


def get_mixamo_bone_name(smplh_joint: str, use_prefix: bool = True) -> str:
    """
    Get the Mixamo bone name for a given SMPL-H joint.

    Args:
        smplh_joint: SMPL-H joint name (e.g., "pelvis")
        use_prefix: Whether to use "mixamorig:" prefix

    Returns:
        Mixamo bone name (e.g., "mixamorig:Hips" or "Hips")
    """
    mixamo_name = SMPLH_TO_MIXAMO.get(smplh_joint)
    if mixamo_name is None:
        return None

    if use_prefix:
        return f"mixamorig:{mixamo_name}"
    return mixamo_name


def get_smplh_joint_index(joint_name: str) -> int | None:
    """Get the index of an SMPL-H joint by name."""
    try:
        return SMPLH_JOINT_NAMES.index(joint_name)
    except ValueError:
        return None


def build_joint_mapping(skeleton_bones: list[str]) -> dict[int, str]:
    """
    Build a mapping from SMPL-H joint indices to FBX bone names.

    Args:
        skeleton_bones: List of bone names from the FBX skeleton

    Returns:
        Dict mapping SMPL-H joint index -> FBX bone name
    """
    # Determine if bones use mixamorig: prefix
    use_prefix = any(bone.startswith("mixamorig:") for bone in skeleton_bones)

    mapping = {}
    for idx, smplh_name in enumerate(SMPLH_JOINT_NAMES):
        mixamo_name = get_mixamo_bone_name(smplh_name, use_prefix=use_prefix)
        if mixamo_name and mixamo_name in skeleton_bones:
            mapping[idx] = mixamo_name

    return mapping
