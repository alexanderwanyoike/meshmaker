"""Retarget SMPL-H motion from HY-Motion onto a UniRig armature in Blender.

Decodes the base64-encoded numpy arrays returned by the RunPod handler,
converts 6D rotations to matrices, runs forward kinematics, and bakes
keyframes onto the target armature using the fast fcurves API.
"""

import base64
import io
import math

import numpy as np

# ---------------------------------------------------------------------------
# SMPL-H skeleton constants (52 joints: 22 body + 30 finger)
# ---------------------------------------------------------------------------

SMPLH_JOINT_NAMES = [
    "Pelvis", "L_Hip", "R_Hip", "Spine1", "L_Knee", "R_Knee", "Spine2",
    "L_Ankle", "R_Ankle", "Spine3", "L_Foot", "R_Foot", "Neck",
    "L_Collar", "R_Collar", "Head", "L_Shoulder", "R_Shoulder",
    "L_Elbow", "R_Elbow", "L_Wrist", "R_Wrist",
    # Fingers (22-51)
    "L_Index1", "L_Index2", "L_Index3",
    "L_Middle1", "L_Middle2", "L_Middle3",
    "L_Pinky1", "L_Pinky2", "L_Pinky3",
    "L_Ring1", "L_Ring2", "L_Ring3",
    "L_Thumb1", "L_Thumb2", "L_Thumb3",
    "R_Index1", "R_Index2", "R_Index3",
    "R_Middle1", "R_Middle2", "R_Middle3",
    "R_Pinky1", "R_Pinky2", "R_Pinky3",
    "R_Ring1", "R_Ring2", "R_Ring3",
    "R_Thumb1", "R_Thumb2", "R_Thumb3",
]

SMPLH_PARENTS = [
    -1,  # 0  Pelvis
     0,  # 1  L_Hip
     0,  # 2  R_Hip
     0,  # 3  Spine1
     1,  # 4  L_Knee
     2,  # 5  R_Knee
     3,  # 6  Spine2
     4,  # 7  L_Ankle
     5,  # 8  R_Ankle
     6,  # 9  Spine3
     7,  # 10 L_Foot
     8,  # 11 R_Foot
     9,  # 12 Neck
     9,  # 13 L_Collar
     9,  # 14 R_Collar
    12,  # 15 Head
    13,  # 16 L_Shoulder
    14,  # 17 R_Shoulder
    16,  # 18 L_Elbow
    17,  # 19 R_Elbow
    18,  # 20 L_Wrist
    19,  # 21 R_Wrist
    20,  # 22 L_Index1
    22,  # 23 L_Index2
    23,  # 24 L_Index3
    20,  # 25 L_Middle1
    25,  # 26 L_Middle2
    26,  # 27 L_Middle3
    20,  # 28 L_Pinky1
    28,  # 29 L_Pinky2
    29,  # 30 L_Pinky3
    20,  # 31 L_Ring1
    31,  # 32 L_Ring2
    32,  # 33 L_Ring3
    20,  # 34 L_Thumb1
    34,  # 35 L_Thumb2
    35,  # 36 L_Thumb3
    21,  # 37 R_Index1
    37,  # 38 R_Index2
    38,  # 39 R_Index3
    21,  # 40 R_Middle1
    40,  # 41 R_Middle2
    41,  # 42 R_Middle3
    21,  # 43 R_Pinky1
    43,  # 44 R_Pinky2
    44,  # 45 R_Pinky3
    21,  # 46 R_Ring1
    46,  # 47 R_Ring2
    47,  # 48 R_Ring3
    21,  # 49 R_Thumb1
    49,  # 50 R_Thumb2
    50,  # 51 R_Thumb3
]

# SMPL-H joint index → UniRig bone name (from ARTICULATION_MAPPING)
SMPLH_TO_UNIRIG = {
     0: "bone_0",    # Pelvis
     1: "bone_44",   # L_Hip
     2: "bone_48",   # R_Hip
     3: "bone_1",    # Spine1
     4: "bone_45",   # L_Knee
     5: "bone_49",   # R_Knee
     6: "bone_2",    # Spine2
     7: "bone_46",   # L_Ankle
     8: "bone_50",   # R_Ankle
     9: "bone_3",    # Spine3
    10: "bone_47",   # L_Foot
    11: "bone_51",   # R_Foot
    12: "bone_4",    # Neck
    13: "bone_6",    # L_Collar
    14: "bone_25",   # R_Collar
    15: "bone_5",    # Head
    16: "bone_7",    # L_Shoulder
    17: "bone_26",   # R_Shoulder
    18: "bone_8",    # L_Elbow
    19: "bone_27",   # R_Elbow
    20: "bone_9",    # L_Wrist
    21: "bone_28",   # R_Wrist
    22: "bone_13",   # L_Index1
    23: "bone_14",   # L_Index2
    24: "bone_15",   # L_Index3
    25: "bone_16",   # L_Middle1
    26: "bone_17",   # L_Middle2
    27: "bone_18",   # L_Middle3
    28: "bone_22",   # L_Pinky1
    29: "bone_23",   # L_Pinky2
    30: "bone_24",   # L_Pinky3
    31: "bone_19",   # L_Ring1
    32: "bone_20",   # L_Ring2
    33: "bone_21",   # L_Ring3
    34: "bone_10",   # L_Thumb1
    35: "bone_11",   # L_Thumb2
    36: "bone_12",   # L_Thumb3
    37: "bone_32",   # R_Index1
    38: "bone_33",   # R_Index2
    39: "bone_34",   # R_Index3
    40: "bone_35",   # R_Middle1
    41: "bone_36",   # R_Middle2
    42: "bone_37",   # R_Middle3
    43: "bone_41",   # R_Pinky1
    44: "bone_42",   # R_Pinky2
    45: "bone_43",   # R_Pinky3
    46: "bone_38",   # R_Ring1
    47: "bone_39",   # R_Ring2
    48: "bone_40",   # R_Ring3
    49: "bone_29",   # R_Thumb1
    50: "bone_30",   # R_Thumb2
    51: "bone_31",   # R_Thumb3
}

# Mean hand poses in axis-angle (15 joints × 3 = 45 values each)
LEFT_HAND_MEAN_AA = np.array([
    0.1117,  0.0429, -0.4164,  0.1088, -0.0660, -0.7562,
   -0.0964, -0.0909, -0.1885, -0.1181,  0.0509, -0.5296,
   -0.1437,  0.0552, -0.7049, -0.0192, -0.0923, -0.3379,
   -0.4570, -0.1963, -0.6255, -0.2147, -0.0660, -0.5069,
   -0.3697, -0.0603, -0.0795, -0.1419, -0.0859, -0.6355,
   -0.3033, -0.0579, -0.6314, -0.1761, -0.1321, -0.3734,
    0.8510,  0.2769, -0.0915, -0.4998,  0.0266,  0.0529,
    0.5356,  0.0460, -0.2774,
])

RIGHT_HAND_MEAN_AA = np.array([
    0.1117, -0.0429,  0.4164,  0.1088,  0.0660,  0.7562,
   -0.0964,  0.0909,  0.1885, -0.1181, -0.0509,  0.5296,
   -0.1437, -0.0552,  0.7049, -0.0192,  0.0923,  0.3379,
   -0.4570,  0.1963,  0.6255, -0.2147,  0.0660,  0.5069,
   -0.3697,  0.0603,  0.0795, -0.1419,  0.0859,  0.6355,
   -0.3033,  0.0579,  0.6314, -0.1761,  0.1321,  0.3734,
    0.8510, -0.2769,  0.0915, -0.4998, -0.0266, -0.0529,
    0.5356, -0.0460,  0.2774,
])

# Number of body joints (before fingers)
NUM_BODY_JOINTS = 22
NUM_TOTAL_JOINTS = 52


# ---------------------------------------------------------------------------
# Math helpers (numpy + Blender mathutils only, no scipy)
# ---------------------------------------------------------------------------

def rot6d_to_matrices(rot6d):
    """Convert 6D rotation representation to 3×3 rotation matrices.

    Uses Gram-Schmidt orthonormalisation.

    Args:
        rot6d: array of shape (..., 6)

    Returns:
        array of shape (..., 3, 3)
    """
    a1 = rot6d[..., :3]
    a2 = rot6d[..., 3:6]

    b1 = a1 / (np.linalg.norm(a1, axis=-1, keepdims=True) + 1e-8)

    dot = np.sum(b1 * a2, axis=-1, keepdims=True)
    b2 = a2 - dot * b1
    b2 = b2 / (np.linalg.norm(b2, axis=-1, keepdims=True) + 1e-8)

    b3 = np.cross(b1, b2)

    return np.stack([b1, b2, b3], axis=-1)


def axis_angle_to_matrices(aa):
    """Convert axis-angle vectors to 3×3 rotation matrices (Rodrigues).

    Args:
        aa: array of shape (N, 3)

    Returns:
        array of shape (N, 3, 3)
    """
    angles = np.linalg.norm(aa, axis=-1, keepdims=True)  # (N, 1)
    axes = np.where(angles > 1e-8, aa / angles, np.array([1.0, 0.0, 0.0]))  # (N, 3)
    angles = angles[..., 0]  # (N,)

    c = np.cos(angles)
    s = np.sin(angles)
    t = 1.0 - c

    x = axes[:, 0]
    y = axes[:, 1]
    z = axes[:, 2]

    # Rodrigues formula components
    matrices = np.empty((len(aa), 3, 3), dtype=np.float64)
    matrices[:, 0, 0] = t * x * x + c
    matrices[:, 0, 1] = t * x * y - s * z
    matrices[:, 0, 2] = t * x * z + s * y
    matrices[:, 1, 0] = t * x * y + s * z
    matrices[:, 1, 1] = t * y * y + c
    matrices[:, 1, 2] = t * y * z - s * x
    matrices[:, 2, 0] = t * x * z - s * y
    matrices[:, 2, 1] = t * y * z + s * x
    matrices[:, 2, 2] = t * z * z + c

    return matrices


def forward_kinematics(local_rots, parents):
    """Compute world-space rotations from local rotations via FK.

    Args:
        local_rots: (T, J, 3, 3) local rotation matrices
        parents: list of parent indices (length J), root parent = -1

    Returns:
        (T, J, 3, 3) world rotation matrices
    """
    T, J = local_rots.shape[:2]
    world = np.empty_like(local_rots)

    for j in range(J):
        p = parents[j]
        if p < 0:
            world[:, j] = local_rots[:, j]
        else:
            world[:, j] = world[:, p] @ local_rots[:, j]

    return world


# ---------------------------------------------------------------------------
# Decode RunPod response
# ---------------------------------------------------------------------------

def _decode_numpy(encoded):
    """Decode a single base64-encoded numpy array from the RunPod handler.

    The handler encodes with ``np.save()`` into a BytesIO, so we try
    ``np.load()`` first.  Falls back to ``np.frombuffer`` if that fails.
    """
    raw = base64.b64decode(encoded["data"])
    try:
        return np.load(io.BytesIO(raw), allow_pickle=False)
    except Exception:
        dtype = np.dtype(encoded.get("dtype", "float32"))
        shape = tuple(encoded["shape"])
        return np.frombuffer(raw, dtype=dtype).reshape(shape)


def decode_motion_arrays(motion_data):
    """Decode the ``motion_data`` dict from the RunPod response.

    Returns:
        (rot6d, transl, fps, num_frames) where rot6d is (T, J, 6) and
        transl is (T, 3).
    """
    def _get(key):
        v = motion_data[key]
        if isinstance(v, dict) and "data" in v:
            return _decode_numpy(v)
        return np.asarray(v)

    rot6d = _get("rot6d")         # (T, J, 6)
    transl = _get("transl")       # (T, 3)
    fps = int(motion_data.get("fps", 30))
    num_frames = int(motion_data.get("num_frames", rot6d.shape[0]))

    return rot6d, transl, fps, num_frames


# ---------------------------------------------------------------------------
# Main retarget entry point
# ---------------------------------------------------------------------------

def apply_motion(armature, result):
    """Apply HY-Motion SMPL-H motion data onto a UniRig armature.

    Called from the operator on the main thread after the RunPod job
    completes.

    Args:
        armature: Blender armature object (with ``bone_0`` etc.)
        result: The ``output`` dict from ``call_runpod()``.

    Returns:
        Number of frames baked.
    """
    import bpy
    from mathutils import Matrix, Quaternion

    # ------------------------------------------------------------------
    # 1. Decode arrays
    # ------------------------------------------------------------------
    rot6d, transl, fps, num_frames = decode_motion_arrays(result["motion_data"])

    # ------------------------------------------------------------------
    # 2. Convert body rot6d → rotation matrices  (T, 22, 3, 3)
    # ------------------------------------------------------------------
    num_body = min(rot6d.shape[1], NUM_BODY_JOINTS)
    body_rot6d = rot6d[:, :num_body]                       # (T, 22, 6)
    body_mats = rot6d_to_matrices(body_rot6d)              # (T, 22, 3, 3)

    # ------------------------------------------------------------------
    # 3. Build full (T, 52, 3, 3) local rotations
    #    Body joints from rot6d; hands from mean pose (static)
    # ------------------------------------------------------------------
    T = body_mats.shape[0]
    local_rots = np.zeros((T, NUM_TOTAL_JOINTS, 3, 3), dtype=np.float64)
    # Identity init for safety
    for j in range(NUM_TOTAL_JOINTS):
        local_rots[:, j] = np.eye(3)

    local_rots[:, :num_body] = body_mats

    # Static hand pose from mean axis-angle
    left_aa = LEFT_HAND_MEAN_AA.reshape(15, 3)
    right_aa = RIGHT_HAND_MEAN_AA.reshape(15, 3)
    left_mats = axis_angle_to_matrices(left_aa)            # (15, 3, 3)
    right_mats = axis_angle_to_matrices(right_aa)          # (15, 3, 3)

    # Finger indices in SMPL-H: left 22-36, right 37-51
    for i in range(15):
        local_rots[:, 22 + i] = left_mats[i]
        local_rots[:, 37 + i] = right_mats[i]

    # ------------------------------------------------------------------
    # 4. Forward kinematics → world rotations (T, 52, 3, 3)
    # ------------------------------------------------------------------
    world_rots = forward_kinematics(local_rots, SMPLH_PARENTS)

    # ------------------------------------------------------------------
    # 5. Y-up → Z-up correction on root (rotate -90° around X)
    # ------------------------------------------------------------------
    cos90 = 0.0
    sin90 = -1.0  # -90 degrees
    yup_to_zup = np.array([
        [1,     0,    0],
        [0, cos90, -sin90],
        [0, sin90,  cos90],
    ], dtype=np.float64)

    for t in range(T):
        world_rots[t, 0] = yup_to_zup @ world_rots[t, 0]

    # ------------------------------------------------------------------
    # 6. Build bone mapping (only bones present in the armature)
    # ------------------------------------------------------------------
    bones = armature.data.bones
    bone_mapping = {}  # smplh_idx → bone_name
    for smplh_idx, bone_name in SMPLH_TO_UNIRIG.items():
        if bone_name in bones:
            bone_mapping[smplh_idx] = bone_name

    if not bone_mapping:
        raise RuntimeError("No matching bones found in armature")

    # ------------------------------------------------------------------
    # 7. Extract UniRig rest-pose world rotations
    # ------------------------------------------------------------------
    # bone.matrix_local is the bone-to-armature-space matrix (rest pose)
    unirig_rest_world = {}   # bone_name → 3×3 np array
    unirig_rest_world_inv = {}
    unirig_parent_bone = {}  # bone_name → parent bone_name or None

    for bone_name in bone_mapping.values():
        bone = bones[bone_name]
        m = np.array(bone.matrix_local.to_3x3())
        unirig_rest_world[bone_name] = m
        unirig_rest_world_inv[bone_name] = np.linalg.inv(m)
        if bone.parent:
            unirig_parent_bone[bone_name] = bone.parent.name
        else:
            unirig_parent_bone[bone_name] = None

    # ------------------------------------------------------------------
    # 8. Compute rest-pose offsets
    #    SMPL-H rest pose is identity for all joints.
    #    offset[j] = smplh_rest_inv @ unirig_rest = I @ unirig_rest
    #              = unirig_rest
    # ------------------------------------------------------------------
    offsets = {}  # bone_name → 3×3
    for smplh_idx, bone_name in bone_mapping.items():
        offsets[bone_name] = unirig_rest_world[bone_name].copy()

    # ------------------------------------------------------------------
    # 9. Compute per-frame target rotations
    #    target_world[j] = source_world[j] @ offset[j]
    #    Then convert world → local using parent chain
    # ------------------------------------------------------------------
    # Pre-compute per-frame target quaternions for each mapped bone
    target_quats = {}   # bone_name → list of (w, x, y, z) per frame
    root_locs = []      # list of (x, y, z) per frame

    for t in range(T):
        for smplh_idx, bone_name in bone_mapping.items():
            target_w = world_rots[t, smplh_idx] @ offsets[bone_name]

            # World → local: local = parent_world_inv @ target_world
            parent_name = unirig_parent_bone[bone_name]
            if parent_name and parent_name in unirig_rest_world_inv:
                # Find the parent's target world rotation this frame
                # We need the parent's SMPLH index
                parent_smplh = None
                for si, bn in bone_mapping.items():
                    if bn == parent_name:
                        parent_smplh = si
                        break

                if parent_smplh is not None:
                    parent_target_w = world_rots[t, parent_smplh] @ offsets[parent_name]
                    parent_inv = np.linalg.inv(parent_target_w)
                    local_rot = parent_inv @ target_w
                else:
                    # Parent bone exists but isn't mapped — use rest pose
                    parent_rest_inv = unirig_rest_world_inv[parent_name]
                    local_rot = parent_rest_inv @ target_w
            else:
                # Root bone or no parent in mapping
                local_rot = target_w

            # Convert 3×3 to quaternion via mathutils
            m4 = Matrix((
                (local_rot[0, 0], local_rot[0, 1], local_rot[0, 2], 0),
                (local_rot[1, 0], local_rot[1, 1], local_rot[1, 2], 0),
                (local_rot[2, 0], local_rot[2, 1], local_rot[2, 2], 0),
                (0, 0, 0, 1),
            ))
            q = m4.to_quaternion()

            if bone_name not in target_quats:
                target_quats[bone_name] = []
            target_quats[bone_name].append((q.w, q.x, q.y, q.z))

    # Root translation: Y-up → Z-up: (x, y, z) → (x, z, -y)
    for t in range(T):
        tx, ty, tz = float(transl[t, 0]), float(transl[t, 1]), float(transl[t, 2])
        root_locs.append((tx, tz, -ty))

    # ------------------------------------------------------------------
    # 10. Create Action and bake keyframes via fcurves (fast path)
    # ------------------------------------------------------------------
    action_name = f"AnimMaker_{armature.name}"
    action = bpy.data.actions.new(name=action_name)
    armature.animation_data_create()
    armature.animation_data.action = action

    root_bone_name = bone_mapping.get(0)

    for bone_name, quats in target_quats.items():
        data_path = f'pose.bones["{bone_name}"].rotation_quaternion'

        # Create 4 fcurves for W, X, Y, Z
        fcs = []
        for ch in range(4):
            fc = action.fcurves.new(data_path=data_path, index=ch)
            fc.keyframe_points.add(count=T)
            fcs.append(fc)

        # Batch-write keyframe data
        for t in range(T):
            frame = t + 1  # Blender frames are 1-based
            for ch in range(4):
                kp = fcs[ch].keyframe_points[t]
                kp.co = (frame, quats[t][ch])
                kp.interpolation = 'LINEAR'

    # ------------------------------------------------------------------
    # 11. Root bone: bake location keyframes from transl
    # ------------------------------------------------------------------
    if root_bone_name:
        loc_path = f'pose.bones["{root_bone_name}"].location'
        loc_fcs = []
        for ch in range(3):
            fc = action.fcurves.new(data_path=loc_path, index=ch)
            fc.keyframe_points.add(count=T)
            loc_fcs.append(fc)

        for t in range(T):
            frame = t + 1
            for ch in range(3):
                kp = loc_fcs[ch].keyframe_points[t]
                kp.co = (frame, root_locs[t][ch])
                kp.interpolation = 'LINEAR'

    # ------------------------------------------------------------------
    # 12. Set scene FPS and frame range
    # ------------------------------------------------------------------
    scene = bpy.context.scene
    scene.render.fps = fps
    scene.frame_start = 1
    scene.frame_end = T
    scene.frame_current = 1

    # Ensure pose bones use quaternion rotation mode
    for bone_name in target_quats:
        pb = armature.pose.bones.get(bone_name)
        if pb:
            pb.rotation_mode = 'QUATERNION'

    return T
