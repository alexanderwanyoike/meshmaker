"""
Thin wrapper around retarget_fbx for server-side SMPL-H → Mixamo retargeting.

Saves motion_data arrays to a temp NPZ, calls retarget_fbx(), returns FBX bytes.
"""

import os
import tempfile
from typing import Any

import numpy as np

from .retarget_fbx import retarget_fbx


# Keys from motion_data that are numpy arrays needed by retarget_fbx's load_npz
_NPZ_KEYS = ("keypoints3d", "rot6d", "transl", "root_rotations_mat")


def retarget_motion_to_fbx(motion_data: dict[str, Any], input_fbx_bytes: bytes) -> bytes:
    """
    Retarget SMPL-H motion data to a Mixamo-rigged FBX character.

    Args:
        motion_data: Dict from generate_motion() containing numpy arrays
            (keypoints3d, rot6d, transl, root_rotations_mat) plus scalars.
        input_fbx_bytes: Raw bytes of the input Mixamo FBX file.

    Returns:
        Bytes of the animated FBX file.
    """
    tmpdir = tempfile.mkdtemp(prefix="retarget_")
    npz_path = os.path.join(tmpdir, "motion.npz")
    fbx_path = os.path.join(tmpdir, "input.fbx")
    out_path = os.path.join(tmpdir, "output.fbx")

    try:
        # Save numpy arrays to NPZ (skip scalars like fps, duration, num_frames)
        arrays = {k: np.asarray(v) for k, v in motion_data.items()
                  if k in _NPZ_KEYS and v is not None}
        np.savez(npz_path, **arrays)

        # Save input FBX
        with open(fbx_path, "wb") as f:
            f.write(input_fbx_bytes)

        # Run the production retargeting pipeline
        retarget_fbx(npz_path, fbx_path, out_path)

        # Read result
        with open(out_path, "rb") as f:
            return f.read()

    finally:
        # Cleanup temp files
        for p in (npz_path, fbx_path, out_path):
            if os.path.exists(p):
                os.unlink(p)
        if os.path.exists(tmpdir):
            os.rmdir(tmpdir)
