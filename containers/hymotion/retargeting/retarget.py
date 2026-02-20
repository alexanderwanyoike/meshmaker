"""
Main retargeting logic for converting SMPL-H motion to Mixamo FBX animation.
"""

import os
import tempfile
from typing import Any

import numpy as np

from .skeleton_mapping import SMPLH_JOINT_NAMES, build_joint_mapping
from .rotation_utils import rot6d_to_euler
from .fbx_io import load_fbx, is_mixamo_rig, apply_animation_to_fbx, save_fbx, cleanup_fbx


def retarget_motion_to_fbx(motion_data: dict[str, Any], input_fbx_bytes: bytes) -> bytes:
    """
    Retarget SMPL-H motion data to a Mixamo-rigged FBX character.

    Args:
        motion_data: Dict containing motion output from HY-Motion, must include:
            - rot6d: (num_frames, num_joints, 6) 6D rotation representation
            - transl: (num_frames, 3) root translation (optional)
            - fps: frames per second
        input_fbx_bytes: Raw bytes of the input Mixamo FBX file

    Returns:
        Bytes of the animated FBX file

    Raises:
        ValueError: If input data is invalid or FBX is not Mixamo-compatible
    """
    # Validate motion data
    if "rot6d" not in motion_data:
        raise ValueError("Motion data missing required 'rot6d' field")

    rot6d = motion_data["rot6d"]
    if isinstance(rot6d, dict) and "data" in rot6d:
        # Decode base64 numpy array
        import base64
        import io
        rot6d = np.load(io.BytesIO(base64.b64decode(rot6d["data"])))

    rot6d = np.asarray(rot6d)

    # Get translation if available
    transl = motion_data.get("transl")
    if transl is not None:
        if isinstance(transl, dict) and "data" in transl:
            import base64
            import io
            transl = np.load(io.BytesIO(base64.b64decode(transl["data"])))
        transl = np.asarray(transl)

    fps = motion_data.get("fps", 30.0)

    # Write input FBX to temp file
    with tempfile.NamedTemporaryFile(suffix=".fbx", delete=False) as f:
        input_path = f.name
        f.write(input_fbx_bytes)

    manager = None
    try:
        # Load and validate FBX
        manager, scene, bone_dict = load_fbx(input_path)
        bone_names = list(bone_dict.keys())

        if not is_mixamo_rig(bone_names):
            raise ValueError(
                "Input FBX is not Mixamo-compatible. "
                f"Found bones: {bone_names[:10]}..."
            )

        # Build joint mapping
        joint_mapping = build_joint_mapping(bone_names)

        if not joint_mapping:
            raise ValueError("Could not map any SMPL-H joints to FBX bones")

        # Convert 6D rotations to Euler angles
        # rot6d shape: (num_frames, num_joints, 6)
        # euler shape: (num_frames, num_joints, 3)
        euler_rotations = rot6d_to_euler(rot6d)

        # Apply animation to FBX
        apply_animation_to_fbx(
            scene=scene,
            bone_dict=bone_dict,
            joint_mapping=joint_mapping,
            euler_rotations=euler_rotations,
            translations=transl,
            fps=fps,
        )

        # Export to temp file
        with tempfile.NamedTemporaryFile(suffix=".fbx", delete=False) as f:
            output_path = f.name

        if not save_fbx(manager, scene, output_path):
            raise ValueError("Failed to export animated FBX")

        # Read output file
        with open(output_path, "rb") as f:
            output_bytes = f.read()

        return output_bytes

    finally:
        # Cleanup
        if manager is not None:
            cleanup_fbx(manager)

        # Remove temp files
        if os.path.exists(input_path):
            os.unlink(input_path)
        if "output_path" in locals() and os.path.exists(output_path):
            os.unlink(output_path)
