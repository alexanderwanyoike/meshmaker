"""
FBX file I/O operations using fbxsdkpy.

Handles loading, validating, and exporting FBX files with animation data.
"""

from __future__ import annotations

import tempfile
import os
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    import fbx

from .skeleton_mapping import MIXAMO_REQUIRED_BONES


def _get_fbx_manager_and_scene():
    """Create and return FBX manager and scene objects."""
    import fbx as fbxsdk

    manager = fbxsdk.FbxManager.Create()
    ios = fbxsdk.FbxIOSettings.Create(manager, fbxsdk.IOSROOT)
    manager.SetIOSettings(ios)

    scene = fbxsdk.FbxScene.Create(manager, "")
    return manager, scene


def load_fbx(fbx_path: str) -> tuple["fbx.FbxManager", "fbx.FbxScene", dict[str, "fbx.FbxNode"]]:
    """
    Load an FBX file and extract the skeleton hierarchy.

    Args:
        fbx_path: Path to the FBX file

    Returns:
        Tuple of (manager, scene, bone_dict) where bone_dict maps bone names to FbxNode objects

    Raises:
        ValueError: If FBX file cannot be loaded
    """
    import fbx as fbxsdk

    manager, scene = _get_fbx_manager_and_scene()

    # Create importer
    importer = fbxsdk.FbxImporter.Create(manager, "")

    if not importer.Initialize(fbx_path, -1, manager.GetIOSettings()):
        error = importer.GetStatus().GetErrorString()
        manager.Destroy()
        raise ValueError(f"Failed to initialize FBX importer: {error}")

    if not importer.Import(scene):
        error = importer.GetStatus().GetErrorString()
        importer.Destroy()
        manager.Destroy()
        raise ValueError(f"Failed to import FBX file: {error}")

    importer.Destroy()

    # Extract skeleton bones
    bone_dict = {}
    _collect_skeleton_nodes(scene.GetRootNode(), bone_dict)

    return manager, scene, bone_dict


def _collect_skeleton_nodes(node: "fbx.FbxNode", bone_dict: dict[str, "fbx.FbxNode"]):
    """Recursively collect all skeleton nodes from the scene."""
    import fbx as fbxsdk

    if node is None:
        return

    # Check if this node has a skeleton attribute
    # eSkeleton may not be exposed in all fbxsdk versions — fall through to
    # the name-based check below if the attribute lookup fails
    attr = node.GetNodeAttribute()
    if attr is not None:
        try:
            attr_type = attr.GetAttributeType()
            if attr_type == fbxsdk.FbxNodeAttribute.eSkeleton:
                bone_dict[node.GetName()] = node
        except AttributeError:
            pass

    # Also check by name pattern (some FBX files don't have skeleton attributes set)
    name = node.GetName()
    if name.startswith("mixamorig:") or name in MIXAMO_REQUIRED_BONES:
        if name not in bone_dict:
            bone_dict[name] = node

    # Recurse into children
    for i in range(node.GetChildCount()):
        _collect_skeleton_nodes(node.GetChild(i), bone_dict)


def is_mixamo_rig(bone_names: list[str]) -> bool:
    """
    Validate that the skeleton is Mixamo-compatible.

    Args:
        bone_names: List of bone names from the FBX skeleton

    Returns:
        True if the skeleton contains required Mixamo bones
    """
    # Check for mixamorig: prefix
    has_prefix = any(name.startswith("mixamorig:") for name in bone_names)

    # Check required bones
    for required in MIXAMO_REQUIRED_BONES:
        if has_prefix:
            expected = f"mixamorig:{required}"
        else:
            expected = required

        if expected not in bone_names:
            return False

    return True


def apply_animation_to_fbx(
    scene: "fbx.FbxScene",
    bone_dict: dict[str, "fbx.FbxNode"],
    joint_mapping: dict[int, str],
    euler_rotations: np.ndarray,
    translations: np.ndarray,
    fps: float = 30.0,
):
    """
    Apply animation keyframes to the FBX skeleton.

    Args:
        scene: FBX scene object
        bone_dict: Dict mapping bone names to FbxNode objects
        joint_mapping: Dict mapping SMPL-H joint indices to bone names
        euler_rotations: Array of shape (num_frames, num_joints, 3) with Euler angles in degrees
        translations: Array of shape (num_frames, 3) with root translation
        fps: Frames per second for the animation
    """
    import fbx as fbxsdk

    num_frames = euler_rotations.shape[0]

    # Create animation stack and layer
    anim_stack = fbxsdk.FbxAnimStack.Create(scene, "MotionStack")
    anim_layer = fbxsdk.FbxAnimLayer.Create(scene, "MotionLayer")
    anim_stack.AddMember(anim_layer)

    # Set up time
    time = fbxsdk.FbxTime()
    time.SetGlobalTimeMode(fbxsdk.FbxTime.eFrames30 if fps == 30 else fbxsdk.FbxTime.eCustom)

    # Find the root bone (Hips) for translation
    root_bone_name = None
    for idx, bone_name in joint_mapping.items():
        if "Hips" in bone_name:
            root_bone_name = bone_name
            break

    # Apply keyframes to each joint
    for joint_idx, bone_name in joint_mapping.items():
        if bone_name not in bone_dict:
            continue

        bone_node = bone_dict[bone_name]

        # Get or create animation curves for rotation
        curve_rx = bone_node.LclRotation.GetCurve(anim_layer, "X", True)
        curve_ry = bone_node.LclRotation.GetCurve(anim_layer, "Y", True)
        curve_rz = bone_node.LclRotation.GetCurve(anim_layer, "Z", True)

        curve_rx.KeyModifyBegin()
        curve_ry.KeyModifyBegin()
        curve_rz.KeyModifyBegin()

        for frame in range(num_frames):
            time.SetFrame(frame, fbxsdk.FbxTime.eFrames30)

            rx, ry, rz = euler_rotations[frame, joint_idx]

            # Add rotation keyframes
            key_index = curve_rx.KeyAdd(time)[0]
            curve_rx.KeySetValue(key_index, rx)
            curve_rx.KeySetInterpolation(key_index, fbxsdk.FbxAnimCurveDef.eInterpolationLinear)

            key_index = curve_ry.KeyAdd(time)[0]
            curve_ry.KeySetValue(key_index, ry)
            curve_ry.KeySetInterpolation(key_index, fbxsdk.FbxAnimCurveDef.eInterpolationLinear)

            key_index = curve_rz.KeyAdd(time)[0]
            curve_rz.KeySetValue(key_index, rz)
            curve_rz.KeySetInterpolation(key_index, fbxsdk.FbxAnimCurveDef.eInterpolationLinear)

        curve_rx.KeyModifyEnd()
        curve_ry.KeyModifyEnd()
        curve_rz.KeyModifyEnd()

        # Apply translation only to root bone
        if bone_name == root_bone_name and translations is not None:
            curve_tx = bone_node.LclTranslation.GetCurve(anim_layer, "X", True)
            curve_ty = bone_node.LclTranslation.GetCurve(anim_layer, "Y", True)
            curve_tz = bone_node.LclTranslation.GetCurve(anim_layer, "Z", True)

            curve_tx.KeyModifyBegin()
            curve_ty.KeyModifyBegin()
            curve_tz.KeyModifyBegin()

            for frame in range(num_frames):
                time.SetFrame(frame, fbxsdk.FbxTime.eFrames30)

                tx, ty, tz = translations[frame]
                # Scale translation (SMPL uses meters, FBX typically uses cm)
                scale = 100.0

                key_index = curve_tx.KeyAdd(time)[0]
                curve_tx.KeySetValue(key_index, tx * scale)
                curve_tx.KeySetInterpolation(key_index, fbxsdk.FbxAnimCurveDef.eInterpolationLinear)

                key_index = curve_ty.KeyAdd(time)[0]
                curve_ty.KeySetValue(key_index, ty * scale)
                curve_ty.KeySetInterpolation(key_index, fbxsdk.FbxAnimCurveDef.eInterpolationLinear)

                key_index = curve_tz.KeyAdd(time)[0]
                curve_tz.KeySetValue(key_index, tz * scale)
                curve_tz.KeySetInterpolation(key_index, fbxsdk.FbxAnimCurveDef.eInterpolationLinear)

            curve_tx.KeyModifyEnd()
            curve_ty.KeyModifyEnd()
            curve_tz.KeyModifyEnd()


def save_fbx(manager: "fbx.FbxManager", scene: "fbx.FbxScene", output_path: str) -> bool:
    """
    Export the FBX scene to a file.

    Args:
        manager: FBX manager object
        scene: FBX scene object
        output_path: Path for the output FBX file

    Returns:
        True if export succeeded
    """
    import fbx as fbxsdk

    # Create exporter
    exporter = fbxsdk.FbxExporter.Create(manager, "")

    # Get FBX binary format
    file_format = -1
    format_count = manager.GetIOPluginRegistry().GetWriterFormatCount()
    for i in range(format_count):
        if manager.GetIOPluginRegistry().WriterIsFBX(i):
            desc = manager.GetIOPluginRegistry().GetWriterFormatDescription(i)
            if "binary" in desc.lower():
                file_format = i
                break

    if file_format < 0:
        file_format = manager.GetIOPluginRegistry().GetNativeWriterFormat()

    if not exporter.Initialize(output_path, file_format, manager.GetIOSettings()):
        error = exporter.GetStatus().GetErrorString()
        exporter.Destroy()
        raise ValueError(f"Failed to initialize FBX exporter: {error}")

    success = exporter.Export(scene)
    exporter.Destroy()

    return success


def cleanup_fbx(manager: "fbx.FbxManager"):
    """Clean up FBX resources."""
    if manager is not None:
        manager.Destroy()
