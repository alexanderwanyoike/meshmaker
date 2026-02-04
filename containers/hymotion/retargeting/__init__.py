"""
Retargeting module for HY-Motion.

Converts SMPL-H motion data to animated Mixamo-rigged FBX files.
"""

from .retarget import retarget_motion_to_fbx

__all__ = ["retarget_motion_to_fbx"]
