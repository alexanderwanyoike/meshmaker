"""
Rotation conversion utilities for motion retargeting.

Converts between:
- 6D rotation representation (from HY-Motion)
- 3x3 rotation matrices
- Euler angles (XYZ order, degrees) for FBX
"""

import numpy as np


def rotation_6d_to_matrix(rot6d: np.ndarray) -> np.ndarray:
    """
    Convert 6D rotation representation to 3x3 rotation matrix using Gram-Schmidt.

    The 6D representation consists of the first two columns of the rotation matrix.
    We recover the third column via cross product and orthonormalize.

    Args:
        rot6d: Array of shape (..., 6) containing 6D rotations

    Returns:
        Array of shape (..., 3, 3) containing rotation matrices
    """
    # Split into two 3D vectors (first two columns of rotation matrix)
    a1 = rot6d[..., :3]
    a2 = rot6d[..., 3:6]

    # Gram-Schmidt orthonormalization
    # First column: normalize a1
    b1 = a1 / (np.linalg.norm(a1, axis=-1, keepdims=True) + 1e-8)

    # Second column: remove component along b1 from a2, then normalize
    dot = np.sum(b1 * a2, axis=-1, keepdims=True)
    b2 = a2 - dot * b1
    b2 = b2 / (np.linalg.norm(b2, axis=-1, keepdims=True) + 1e-8)

    # Third column: cross product of first two
    b3 = np.cross(b1, b2)

    # Stack into rotation matrix
    # Shape: (..., 3, 3)
    matrix = np.stack([b1, b2, b3], axis=-1)

    return matrix


def matrix_to_euler_xyz(matrix: np.ndarray) -> np.ndarray:
    """
    Convert rotation matrix to Euler angles in XYZ order (degrees).

    This follows the FBX convention where rotations are applied in X, Y, Z order.

    Args:
        matrix: Array of shape (..., 3, 3) containing rotation matrices

    Returns:
        Array of shape (..., 3) containing Euler angles [rx, ry, rz] in degrees
    """
    # Extract elements
    r00 = matrix[..., 0, 0]
    r01 = matrix[..., 0, 1]
    r02 = matrix[..., 0, 2]
    r10 = matrix[..., 1, 0]
    r11 = matrix[..., 1, 1]
    r12 = matrix[..., 1, 2]
    r20 = matrix[..., 2, 0]
    r21 = matrix[..., 2, 1]
    r22 = matrix[..., 2, 2]

    # Check for gimbal lock (when r02 is close to +/- 1)
    sy = np.sqrt(r00**2 + r10**2)

    # Avoid division by zero
    singular = sy < 1e-6

    # Normal case
    x = np.arctan2(r12, r22)
    y = np.arctan2(-r02, sy)
    z = np.arctan2(r01, r00)

    # Gimbal lock case
    x_singular = np.arctan2(-r21, r11)
    y_singular = np.arctan2(-r02, sy)
    z_singular = np.zeros_like(z)

    # Select based on singularity
    x = np.where(singular, x_singular, x)
    y = np.where(singular, y_singular, y)
    z = np.where(singular, z_singular, z)

    # Stack and convert to degrees
    euler = np.stack([x, y, z], axis=-1)
    return np.degrees(euler)


def rot6d_to_euler(rot6d: np.ndarray) -> np.ndarray:
    """
    Convert 6D rotation directly to Euler angles (XYZ order, degrees).

    Args:
        rot6d: Array of shape (..., 6) containing 6D rotations

    Returns:
        Array of shape (..., 3) containing Euler angles in degrees
    """
    matrix = rotation_6d_to_matrix(rot6d)
    return matrix_to_euler_xyz(matrix)
