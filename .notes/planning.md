# Motion Creator - Product Planning

## Vision

Create game-ready animations from text prompts, targeting video game developers.

---

## Research Findings

### HY-Motion Limitations (Critical)

From [HY-Motion GitHub](https://github.com/Tencent-Hunyuan/HY-Motion-1.0):
- **Looping is NOT supported** - marked as ❌ in "Special Modes"
- Outputs SMPL-H format (52 joints, not game-ready)
- No built-in retargeting to game skeletons

This confirms our core problem: HY-Motion generates one-shot animations only.

---

### How Competitors Solve Looping

#### DeepMotion SayMotion V2.4
[Source](https://www.deepmotion.com/post/saymotion-v2-4-loop-refine-rerun)

SayMotion has a dedicated **AI Loop Tool** with these settings:

| Setting | Description |
|---------|-------------|
| **Transition Period** | Time (up to 8s) to blend last→first frame |
| **Root Fix: Locked** | Character stays in place (idle, standing) |
| **Root Fix: Blend Horizontal** | Smooth horizontal position blend (walk/run) |
| **Root Fix: Blend Altitude** | Smooth vertical blend (jumping) |
| **Root Fix: Blend Orientation** | Smooth rotation blend |
| **Fix Root Scope** | Which section of clip gets root fixes |

**Takeaway**: We need similar post-processing. The key is blending + root motion handling.

#### The Orange Duck - Inertialization Technique
[Source](https://theorangeduck.com/page/creating-looping-animations-motion-capture)

Academic/practical approach for looping mocap data:

1. **Core requirement**: First frame = last frame, AND velocities must match
2. **Inertialization**: Spring-based blending to stitch animation with itself
   - Compute position/velocity differences between final and initial frames
   - Add differences as decaying offsets across animation
   - Use critically damped springs or cubic decay
3. **Methods**:
   - **Cubic blending**: Guarantees complete fade-out (best for loops)
   - **Softfade**: Limits adjustments to edges using logarithmic ramping
4. **Root motion**: Handle in local space relative to starting orientation

**Takeaway**: This is implementable. We could add this as post-processing to HY-Motion output.

---

### Skeleton Standards Research

#### The Universal Answer: Mixamo

From multiple sources, **Mixamo is the de-facto standard**:
- Free (Adobe-owned)
- Works with Unity, Unreal, Godot
- Well-documented 65-bone humanoid rig
- Huge animation library for reference
- Auto-rigging available

**Our current pipeline (SMPL-H → Mixamo) is correct.**

#### Engine-Specific Details

| Engine | Skeleton | Retargeting |
|--------|----------|-------------|
| **Unity** | Humanoid/Mecanim | Auto-retargets any humanoid rig |
| **Unreal 5** | SK_Mannequin | IK Rig + IK Retargeter tools |
| **Godot 4** | SkeletonProfileHumanoid | Built-in retargeting since 4.0 |

[Godot docs](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/retargeting_3d_skeletons.html):
> "Mixamo can autorig your character with a game dev skeleton - it's a free and easy option"

#### SMPL → Game Engine Tools

1. **[Meshcapade SMPL Blender Addon](https://github.com/Meshcapade/SMPL_blender_addon)** - Official, supports SMPL-H, can load .npz files with animations
2. **[SMPL-to-FBX](https://github.com/softcat477/SMPL-to-FBX)** - Blender addon for converting SMPL to FBX
3. **[SMPL official site](https://smpl.is.tue.mpg.de/)** - Has sample FBX files and Unity code

---

### Market Context

#### Competition is Coming Fast

- **Unity Muse** - Adding text-to-motion directly in-editor ([Source](https://www.cgchannel.com/2025/03/unity-unveils-its-2025-product-roadmap/))
- **DeepMotion SayMotion** - Already has looping, text-to-3D, retargeting
- **90% of game devs** already use AI in workflows ([Google Cloud Research](https://www.googlecloudpresscorner.com/2025-08-18-90-of-Games-Developers-Already-Using-AI-in-Workflows,-According-to-New-Google-Cloud-Research))

#### What Indie Devs Actually Do

Real workflow from [Meshy case study](https://www.meshy.ai/blog/ai-in-game-development):
1. Generate character concept with AI
2. Image → 3D model (Meshy)
3. **Mixamo for animations** ← we replace this step
4. Import to game engine

> "About an hour or two to actually get the animated model in game. It would have taken me dozens of hours..."

**Opportunity**: Replace Mixamo's limited library with infinite text-to-motion.

---

## Revised Strategy

### Core Differentiator

Mixamo has ~2,500 animations. We offer **infinite** animations via text prompts.

But we MUST match Mixamo's quality:
- ✅ Correct skeleton (Mixamo-compatible)
- ❌ Loopable (NOT YET - critical gap)
- ❌ Root motion options (NOT YET)
- ⚠️ Clean foot contacts (needs validation)

### What We Need to Build

#### Phase 1: Looping (Critical Path)

Implement post-processing loop system inspired by DeepMotion + Orange Duck:

```
Input: Raw HY-Motion output (.npz)
       ↓
Step 1: Find similar poses (if duration > needed)
       OR use full clip
       ↓
Step 2: Inertialization blend
       - Cubic decay for position
       - Velocity matching
       ↓
Step 3: Root motion fix
       - Locked (in-place)
       - Blend horizontal (locomotion)
       ↓
Output: Looped animation (.npz/.fbx)
```

**UI additions:**
- [ ] "Loop" checkbox
- [ ] Loop mode dropdown (Locked / Blend Horizontal)
- [ ] Transition duration slider

#### Phase 2: Multi-Format Export

Support all major engines:
- FBX (universal)
- GLB/GLTF (web, Godot)
- Unity package (optional)

#### Phase 3: Quality Polish

- Foot contact cleanup (IK post-process?)
- Preview before export
- Batch generation

---

## Open Questions

1. **Can prompt engineering help with loops?**
   - Test: "person walking in a seamless loop"
   - Test: "walk cycle, first and last pose identical"
   - Likely won't work, but worth testing

2. **Pose similarity algorithm?**
   - For finding good loop cut points in longer animations
   - Could use joint angle distance metric

3. **Should we compete with DeepMotion or integrate?**
   - DeepMotion is SaaS, we're self-hosted
   - Different target market (privacy-conscious, cost-conscious devs)

4. **Unity Muse timeline?**
   - If Unity ships text-to-motion in 2025, what's our moat?
   - Answer: Open source, self-hosted, no vendor lock-in

---

## Technical Research TODO

- [ ] Test HY-Motion with loop-related prompts
- [ ] Implement basic inertialization algorithm
- [ ] Measure pose similarity between frame 0 and frame N
- [ ] Test Mixamo FBX import in Godot 4, Unity, UE5
- [ ] Profile foot sliding in current output

---

## Resources

### Documentation
- [HY-Motion GitHub](https://github.com/Tencent-Hunyuan/HY-Motion-1.0)
- [DeepMotion SayMotion Loop Feature](https://www.deepmotion.com/post/saymotion-v2-4-loop-refine-rerun)
- [Orange Duck - Looping Animations](https://theorangeduck.com/page/creating-looping-animations-motion-capture)
- [Godot Skeleton Retargeting](https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/retargeting_3d_skeletons.html)
- [Rokoko Loop Animation Guide](https://www.rokoko.com/insights/loop-animation)

### Tools
- [Meshcapade SMPL Blender Addon](https://github.com/Meshcapade/SMPL_blender_addon)
- [SMPL-to-FBX](https://github.com/softcat477/SMPL-to-FBX)
- [Godot Mixamo Libraries](https://github.com/jwelchgames/Godot4-MixamoLibraries)

---

## Notes

_Add observations and findings here as we test_

