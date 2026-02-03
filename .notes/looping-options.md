# Animation Looping - Technical Options

## The Problem

HY-Motion outputs one-shot animations. Frame 0 and Frame N have:
- Different positions
- Different velocities
- When looped, there's a visible "pop"

For game animations (walk cycles, idles), we need seamless loops.

---

## Option 1: Inertialization (Recommended)

**Source:** [The Orange Duck](https://theorangeduck.com/page/creating-looping-animations-motion-capture)

### What It Is

Stitch an animation to itself by computing the difference between first and last frames, then spreading that difference across the animation using a decay function.

### How It Works

```
Step 1: Compute differences
        diff_pos = last_frame_position - first_frame_position
        diff_vel = last_frame_velocity - first_frame_velocity

Step 2: Apply decaying offset to each frame
        For each frame t:
            offset = decay_function(diff_pos, diff_vel, t)
            frame[t].position += offset
```

### The Math (Cubic Decay)

```python
def cubic_decay(x, v, blend_time, t):
    """
    x = initial position difference
    v = initial velocity difference
    blend_time = how long to spread the blend
    t = current time
    """
    t_normalized = clamp(t / blend_time, 0, 1)

    d = x
    c = v * blend_time
    b = -3*d - 2*c
    a = 2*d + c

    return a*t³ + b*t² + c*t + d
```

This guarantees:
- At t=0: offset = x (full difference)
- At t=blend_time: offset = 0 (completely faded)
- Smooth velocity throughout

### Pros
- Mathematically guaranteed to loop
- Preserves original motion character
- Fast to compute
- Works on any animation

### Cons
- Can introduce subtle drift if not careful
- Need to handle root motion separately
- Longer animations need longer blend times

### Complexity
**Low-Medium.** ~100 lines of Python/C++.

---

## Option 2: Dead Blending

**Source:** [The Orange Duck - Dead Blending](https://theorangeduck.com/page/dead-blending)

### What It Is

Instead of computing offsets, extrapolate the animation forward past its end, then crossfade between the extrapolated end and the beginning.

### How It Works

```
Original:     [Frame 0 -------- Frame N]

Dead Blend:   [Frame 0 -------- Frame N --extrapolate--> Frame N+k]
                                         ↓
              Crossfade zone:   [Frame N ... Frame N+k]
                                      ↓ blend with ↓
                                [Frame 0 ... Frame k]
```

### Pros
- Simpler to understand conceptually
- Result always stays between known poses
- Fewer artifacts like knee pops

### Cons
- Linear extrapolation becomes unrealistic quickly
- Can feel "mushy" or damped
- More complex to implement well
- May need neural network for best results

### Complexity
**Medium.** Simple version ~150 lines, good version needs ML.

---

## Option 3: Pose Matching / Loop Point Detection

### What It Is

Instead of forcing the animation to loop at frame N, find two frames in the middle that are already similar, and cut there.

### How It Works

```
Step 1: Generate longer animation (2-3x needed duration)

Step 2: Compute pose similarity matrix
        For each frame pair (i, j):
            similarity[i,j] = distance(pose_i, pose_j)

Step 3: Find best loop points
        Find (i, j) where:
            - similarity[i,j] is low (poses match)
            - j - i ≈ desired_duration

Step 4: Cut and blend at those points
```

### Pose Distance Metric

```python
def pose_distance(pose_a, pose_b):
    total = 0
    for joint in all_joints:
        # Position distance
        pos_dist = ||pose_a.pos[joint] - pose_b.pos[joint]||²

        # Rotation distance (quaternion)
        rot_dist = 1 - |dot(pose_a.rot[joint], pose_b.rot[joint])|

        # Weight important joints higher (hips, feet)
        weight = joint_weights[joint]
        total += weight * (pos_dist + rot_dist)

    return total
```

### Pros
- Can find naturally loopable segments
- Less artificial blending needed
- Works well for rhythmic motions (walk, run)

### Cons
- Requires generating 2-3x more animation
- May not find good loop points
- More compute time
- Duration becomes approximate

### Complexity
**Medium.** ~200 lines, but needs longer generation.

---

## Option 4: Prompt Engineering (Test First!)

### What It Is

Ask HY-Motion to generate a loop directly via prompt.

### Test Prompts

```
"person walking in a perfect loop"
"seamless walk cycle animation"
"walk cycle, first pose equals last pose"
"person walking in place, looping motion"
```

### Pros
- Zero implementation if it works
- Most elegant solution

### Cons
- Probably won't work (HY-Motion docs say loops unsupported)
- Unpredictable results
- No control over loop quality

### Complexity
**None** - just prompt changes.

**Verdict:** Test this first, but don't expect it to work.

---

## Option 5: Hybrid Approach (Best Practice)

Combine multiple techniques:

```
Step 1: Prompt engineering
        Add "looping" hints to prompt (might help slightly)

Step 2: Generate 1.5-2x duration needed

Step 3: Pose matching
        Find best natural loop points

Step 4: Inertialization
        Apply cubic decay blend at cut points

Step 5: Root motion fix
        - "Locked" mode: zero out root translation
        - "Blend" mode: smooth root to create forward motion
```

### Root Motion Modes

| Mode | Use Case | Implementation |
|------|----------|----------------|
| **Locked** | Idle, dance in place | Zero root XZ translation |
| **Blend Horizontal** | Walk, run | Blend root XZ between first/last frame |
| **Blend All** | Jump loops | Blend all root channels |

---

## Comparison Summary

| Option | Complexity | Quality | Reliability | Best For |
|--------|------------|---------|-------------|----------|
| Inertialization | Low-Med | Good | High | General purpose |
| Dead Blending | Medium | Good | Medium | Transitions |
| Pose Matching | Medium | Best | Medium | Rhythmic motion |
| Prompt Engineering | None | Unknown | Low | Quick test |
| Hybrid | High | Best | High | Production |

---

## Recommended Implementation Order

1. **Test prompts first** (5 min) - see if HY-Motion responds to loop hints
2. **Implement basic inertialization** (1-2 days) - cubic decay, handles 80% of cases
3. **Add root motion modes** (0.5 day) - locked vs blend horizontal
4. **Optional: Add pose matching** (1-2 days) - for higher quality

---

## References

- [Creating Looping Animations from Motion Capture](https://theorangeduck.com/page/creating-looping-animations-motion-capture) - Daniel Holden
- [Dead Blending](https://theorangeduck.com/page/dead-blending) - Daniel Holden
- [Inertialization in Gears of War](https://cdn.gearsofwar.com/thecoalition/publications/GDC%202018%20-%20Inertialization%20-%20High%20Performance%20Animation%20Transitions%20in%20Gears%20of%20War.pdf) - GDC 2018
- [DeepMotion SayMotion Loop Feature](https://www.deepmotion.com/post/saymotion-v2-4-loop-refine-rerun)
