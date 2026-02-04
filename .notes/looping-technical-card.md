# Animation Looping: Technical Implementation Card

## TL;DR Decision Matrix

| Approach | Build vs Buy | Complexity | Best For |
|----------|--------------|------------|----------|
| **Inertialization** | Build (no lib exists) | ~150 LOC | General loops |
| **Pose Matching** | Build (use scipy DTW) | ~200 LOC | Finding natural cuts |
| **Hybrid** | Build both | ~300 LOC | Production quality |

**Bottom line:** No Python library does animation looping out of the box. We must implement it, but the building blocks exist.

---

## Available Libraries (Building Blocks)

### 1. PyMotion - Quaternion & Skeleton Ops
```bash
pip install upc-pymotion
```

| Has | Doesn't Have |
|-----|--------------|
| Quaternion ↔ rotation matrix ↔ euler ↔ axis-angle | Looping |
| Forward kinematics | Blending |
| BVH read/write | Inertialization |
| Skeleton mirroring | |
| NumPy + PyTorch backends | |

**Use for:** Rotation math, FK, file I/O

[GitHub](https://github.com/UPC-ViRVIG/pymotion) | [PyPI](https://pypi.org/project/upc-pymotion/)

---

### 2. Fairmotion - Facebook's Motion Lib
```bash
pip install fairmotion
```

| Has | Doesn't Have |
|-----|--------------|
| BVH/ASF/AMC/AMASS loading | Looping |
| Motion slicing (`cut(motion, start, end)`) | Blending |
| Translation ops | Interpolation |
| Matrix-based transforms | |

**Use for:** Loading AMASS data, slicing clips

[GitHub](https://github.com/facebookresearch/fairmotion) ⚠️ Archived May 2023

---

### 3. SciPy - Interpolation Math
```bash
pip install scipy
```

**Key functions:**
```python
from scipy.interpolate import CubicSpline
from scipy.spatial.distance import cdist
from scipy.signal import savgol_filter
```

| Function | Use Case |
|----------|----------|
| `CubicSpline(x, y, bc_type='clamped')` | Smooth blend curves |
| `cdist(poses_a, poses_b, 'euclidean')` | Pose distance matrix |
| `savgol_filter(data, window, poly)` | Smooth jitter |

**Use for:** The actual blending math

---

### 4. dtaidistance - Dynamic Time Warping
```bash
pip install dtaidistance
```

```python
from dtaidistance import dtw
distance = dtw.distance(seq1, seq2)
path = dtw.warping_path(seq1, seq2)
```

**Use for:** Finding similar poses even if timing differs (pose matching)

---

## Inertialization: Full Implementation

### Theory

Given animation where `frame[0] ≠ frame[N]`:

1. Compute difference: `Δpos = frame[N].pos - frame[0].pos`
2. Compute velocity diff: `Δvel = frame[N].vel - frame[0].vel`
3. For each frame `t`, add decaying offset that starts at `Δ` and ends at `0`

### The Math (Cubic Hermite)

```python
def cubic_decay(x: np.ndarray, v: np.ndarray, blend_time: float, t: float) -> np.ndarray:
    """
    Attempt to describe: Computing a decaying offset using cubic polynomial.

    Args:
        x: Initial position difference (frame[N] - frame[0])
        v: Initial velocity difference
        blend_time: Duration over which to spread the blend
        t: Current time in animation

    Returns:
        Offset to add to current frame
    """
    # Normalize time to [0, 1]
    t_norm = np.clip(t / blend_time, 0.0, 1.0)

    # Cubic Hermite coefficients
    # Guarantees: f(0)=x, f(1)=0, f'(0)=v*blend_time, f'(1)=0
    d = x
    c = v * blend_time
    b = -3*d - 2*c
    a = 2*d + c

    # Evaluate cubic: a*t³ + b*t² + c*t + d
    t2 = t_norm * t_norm
    t3 = t2 * t_norm
    return a*t3 + b*t2 + c*t_norm + d
```

### Full Implementation

```python
import numpy as np
from scipy.spatial.transform import Rotation, Slerp

def make_loop_inertialize(
    positions: np.ndarray,  # (frames, joints, 3)
    rotations: np.ndarray,  # (frames, joints, 4) quaternions xyzw
    fps: float = 30.0,
    blend_ratio: float = 0.5,  # Blend over 50% of animation
) -> tuple[np.ndarray, np.ndarray]:
    """
    Make animation loop using inertialization (cubic decay).
    """
    n_frames = positions.shape[0]
    blend_frames = int(n_frames * blend_ratio)
    blend_time = blend_frames / fps

    # --- POSITIONS ---
    # Compute differences
    pos_diff = positions[-1] - positions[0]  # (joints, 3)

    # Estimate velocity at endpoints (finite difference)
    vel_start = (positions[1] - positions[0]) * fps
    vel_end = (positions[-1] - positions[-2]) * fps
    vel_diff = vel_end - vel_start

    # Apply decaying offset to each frame
    positions_looped = positions.copy()
    for i in range(n_frames):
        t = i / fps
        offset = cubic_decay(pos_diff, vel_diff, blend_time, t)
        # Apply more at start, less at end
        positions_looped[i] -= offset

    # --- ROTATIONS ---
    # For quaternions: compute rotation difference, apply slerp decay
    rotations_looped = rotations.copy()
    for j in range(rotations.shape[1]):  # Each joint
        q_start = rotations[0, j]
        q_end = rotations[-1, j]

        # Rotation difference: q_diff = q_end * q_start.inv()
        r_start = Rotation.from_quat(q_start)
        r_end = Rotation.from_quat(q_end)
        r_diff = r_end * r_start.inv()

        for i in range(n_frames):
            t_norm = np.clip(i / blend_frames, 0.0, 1.0)
            # Cubic blend factor (same as position)
            blend = 1.0 - (3*t_norm**2 - 2*t_norm**3)  # Smoothstep inverse

            # Apply partial rotation correction
            r_correction = Rotation.from_rotvec(r_diff.as_rotvec() * blend)
            r_original = Rotation.from_quat(rotations[i, j])
            r_corrected = r_correction.inv() * r_original
            rotations_looped[i, j] = r_corrected.as_quat()

    return positions_looped, rotations_looped
```

### Complexity: ~80 LOC core, ~150 LOC with utils

---

## Pose Matching: Full Implementation

### Theory

Instead of forcing frame[0]=frame[N], find two frames in the middle that are already similar.

1. Generate 2x duration animation
2. Build pose similarity matrix
3. Find `(i, j)` where `similarity[i,j]` is lowest and `j-i ≈ target_duration`
4. Cut at those frames, apply small blend

### Pose Distance Metric

```python
def pose_distance(
    pose_a: np.ndarray,  # (joints, 3) positions
    pose_b: np.ndarray,
    joint_weights: np.ndarray = None,  # Emphasize hips, feet
) -> float:
    """
    Weighted L2 distance between poses.
    """
    if joint_weights is None:
        joint_weights = np.ones(pose_a.shape[0])

    diff = pose_a - pose_b
    squared_dist = np.sum(diff ** 2, axis=1)  # Per joint
    weighted = squared_dist * joint_weights
    return np.sqrt(np.sum(weighted))
```

### Finding Best Loop Points

```python
def find_loop_points(
    positions: np.ndarray,  # (frames, joints, 3)
    target_frames: int,
    tolerance: int = 10,  # ±frames flexibility
    joint_weights: np.ndarray = None,
) -> tuple[int, int, float]:
    """
    Find best (start, end) frames for looping.

    Returns:
        (start_frame, end_frame, similarity_score)
    """
    n_frames = positions.shape[0]

    # Flatten poses for distance computation
    poses_flat = positions.reshape(n_frames, -1)  # (frames, joints*3)

    # Compute pairwise distances
    from scipy.spatial.distance import cdist
    dist_matrix = cdist(poses_flat, poses_flat, 'euclidean')

    # Find minimum in valid range
    best_score = float('inf')
    best_start, best_end = 0, target_frames

    for i in range(n_frames - target_frames - tolerance):
        for j in range(i + target_frames - tolerance,
                       min(i + target_frames + tolerance, n_frames)):
            score = dist_matrix[i, j]
            if score < best_score:
                best_score = score
                best_start, best_end = i, j

    return best_start, best_end, best_score
```

### Complexity: ~100 LOC

---

## Hybrid Approach (Recommended)

```python
def make_loop_hybrid(
    positions: np.ndarray,
    rotations: np.ndarray,
    target_duration: float,
    fps: float = 30.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Best quality: pose match + inertialization.
    """
    target_frames = int(target_duration * fps)
    n_frames = positions.shape[0]

    # Step 1: If we have extra frames, find best cut points
    if n_frames > target_frames * 1.2:
        start, end, score = find_loop_points(positions, target_frames)
        positions = positions[start:end]
        rotations = rotations[start:end]
        print(f"Cut at frames {start}-{end}, similarity={score:.4f}")

    # Step 2: Apply inertialization to smooth the loop
    positions, rotations = make_loop_inertialize(
        positions, rotations, fps, blend_ratio=0.3
    )

    return positions, rotations
```

### Complexity: ~300 LOC total

---

## Root Motion Handling

Critical for game animations:

```python
def apply_root_mode(
    positions: np.ndarray,  # (frames, joints, 3)
    root_joint: int = 0,
    mode: str = 'locked',  # 'locked' | 'blend_horizontal' | 'blend_all'
) -> np.ndarray:
    """
    Fix root motion for game use.
    """
    positions = positions.copy()
    root_pos = positions[:, root_joint, :]  # (frames, 3)

    if mode == 'locked':
        # Zero out XZ movement, keep Y (height)
        root_pos[:, [0, 2]] = root_pos[0, [0, 2]]

    elif mode == 'blend_horizontal':
        # Smooth blend of XZ from start to end
        n = len(root_pos)
        start_xz = root_pos[0, [0, 2]]
        end_xz = root_pos[-1, [0, 2]]
        for i in range(n):
            t = i / (n - 1)
            # Linear blend of the drift
            drift = (end_xz - start_xz) * t
            root_pos[i, [0, 2]] -= drift

    elif mode == 'blend_all':
        # Smooth blend all axes (for jumps)
        n = len(root_pos)
        start = root_pos[0]
        end = root_pos[-1]
        for i in range(n):
            t = i / (n - 1)
            drift = (end - start) * t
            root_pos[i] -= drift

    positions[:, root_joint, :] = root_pos
    return positions
```

---

## Integration with HY-Motion Output

```python
import numpy as np

def process_hymotion_output(npz_path: str, loop: bool = True) -> dict:
    """
    Load HY-Motion .npz and make it game-ready.
    """
    data = np.load(npz_path)

    # HY-Motion outputs: poses (SMPL), trans, betas
    poses = data['poses']      # (frames, 72) - axis-angle
    trans = data['trans']      # (frames, 3)

    # Convert axis-angle to quaternions
    from scipy.spatial.transform import Rotation
    n_frames = poses.shape[0]
    n_joints = 24  # SMPL

    poses_reshaped = poses.reshape(n_frames, n_joints, 3)
    quats = np.zeros((n_frames, n_joints, 4))
    for i in range(n_frames):
        for j in range(n_joints):
            r = Rotation.from_rotvec(poses_reshaped[i, j])
            quats[i, j] = r.as_quat()

    # Get joint positions via forward kinematics
    # (requires SMPL model or pymotion)
    positions = forward_kinematics(quats, trans)  # You implement this

    if loop:
        positions, quats = make_loop_hybrid(positions, quats, ...)
        positions = apply_root_mode(positions, mode='locked')

    return {'positions': positions, 'rotations': quats}
```

---

## Summary: What to Build

| Component | LOC | Dependencies | Priority |
|-----------|-----|--------------|----------|
| `cubic_decay()` | 15 | numpy | P0 |
| `make_loop_inertialize()` | 60 | numpy, scipy.spatial.transform | P0 |
| `pose_distance()` | 10 | numpy | P1 |
| `find_loop_points()` | 40 | scipy.spatial.distance | P1 |
| `apply_root_mode()` | 30 | numpy | P0 |
| `make_loop_hybrid()` | 20 | above | P1 |

**Total: ~175 LOC** for production-ready looping.

---

## References

- [Orange Duck - Creating Looping Animations](https://theorangeduck.com/page/creating-looping-animations-motion-capture)
- [Orange Duck - Dead Blending](https://theorangeduck.com/page/dead-blending)
- [Gears of War Inertialization GDC 2018](https://cdn.gearsofwar.com/thecoalition/publications/GDC%202018%20-%20Inertialization%20-%20High%20Performance%20Animation%20Transitions%20in%20Gears%20of%20War.pdf)
- [PyMotion GitHub](https://github.com/UPC-ViRVIG/pymotion)
- [Fairmotion GitHub](https://github.com/facebookresearch/fairmotion)
- [SciPy CubicSpline](https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.CubicSpline.html)
- [dtaidistance (DTW)](https://pypi.org/project/dtaidistance/)
