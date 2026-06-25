# MeshMaker - Reference

> Distilled model/competitor landscape and positioning notes. Background for backend choices in `cards/`. Not a to-do list. Last refreshed June 2026.

## 1. Generate (image -> mesh)

### Open-source models

| Model | Origin | License | Quality | Notes |
|---|---|---|---|---|
| **Trellis 2** (legacy) | Microsoft | MIT | Very good geometry, darker textures | O-Voxel + DiT. Keep as reference only unless Hunyuan3D 3.5 access fails |
| **Hunyuan3D 2.1** (legacy) | Tencent | Permissive commercial | Better PBR textures than Trellis | Flow-matching DiT + Paint. Keep as reference only unless Hunyuan3D 3.5 access fails |
| **Hunyuan3D 3.5** | Tencent | TBD | Target | Only active Generate target. Access path must be confirmed before implementation |
| **Pixal3D** | TencentARC / Tsinghua | Open | Near-reconstruction fidelity | Deferred. Do not add unless the single-generator plan fails |
| **Hunyuan3D-Omni** | Tencent | Open | Controllable | "ControlNet of 3D": point cloud / voxel / bbox / pose conditioning |
| **TripoSG** | VAST-AI | MIT | High-fidelity shape only | 1.5B rectified flow, no texture |
| **TripoSR / Stable Fast 3D** | VAST-AI / Stability | MIT / community | Lower, very fast | <0.5-1s. Good for previews |

**Current takeaway:** keep Generate scoped to Hunyuan3D 3.5 only. Do not build a Trellis/Pixal3D/Meshy/Tripo A/B harness for the focused build.

### Commercial platforms (the bar / fallback providers)

| Platform | Pricing | Own models | Integrations |
|---|---|---|---|
| **Meshy** | $20/mo, 1000 credits | Meshy-4/5/6 | Blender, Unity, Unreal, Maya, 3ds Max, Godot |
| **Tripo** | $16/mo, 3000 credits | Prism 3.0 | Blender, Unity, Unreal, ComfyUI, Cocos, Godot |
| **Rodin/Hyper3D** | $99/mo | Yes | Photorealistic 4K PBR |
| **3DAI Studio** | $14/mo, 1000 credits | Aggregator | The "router" model, already exists |

These are background market references, not active fallback providers. Do not build Meshy/Tripo routing until the single-generator pipeline works and there is a concrete reason to add a second Generate provider.

## 2. Rig (mesh -> rigged)

| Model | Venue | Scope | Speed | Notes |
|---|---|---|---|---|
| **MIA** (current) | CVPR 2025 | Humanoid only | <1s | 5 PCAE checkpoints predict 52 Mixamo joints + per-vertex skinning + rest pose. Outputs ready-to-animate Mixamo FBX |
| **UniRig** | SIGGRAPH 2025 | Diverse assets | 1-5s | GPT-like skeleton prediction, 14K+ models. Dropped earlier: skeleton format broke HY-Motion retarget |
| **SkinTokens / TokenRig** | Feb 2026 | Unified | TBD | Successor to UniRig. Discrete skin-weight tokens + Qwen3-0.6B transformer. **98-133% skinning / 17-22% bone-prediction improvement.** Rig upgrade target |
| **MagicArticulate** | CVPR 2025 | Articulated objects | 1-2s | 33K+ models, for non-humanoid |

**Why MIA, and the constraint for any swap:** HY-Motion's server-side retarget (`retarget_fbx.py`) maps SMPL-H motion to Mixamo via a 700+ entry bone dict. MIA outputs a native Mixamo skeleton that chains straight in. UniRig didn't, which is why it was dropped. **When swapping MIA -> SkinTokens, the open question is whether its skeleton maps into that retarget path** (or needs a new mapping). MIA's limitation: humanoid only (trained on 95 chars); non-humanoid assets need UniRig/MagicArticulate + a compatible retarget path.

Commercial note: **AccuRIG 2** (free, fully automated, no markers) is excellent but desktop-only, not an API.

## 3. Motion (text -> motion) and Video -> Motion

| Tool | Pricing | OSS | Looping | Editing | Notes |
|---|---|---|---|---|---|
| **HY-Motion** (current) | Free | Yes | No | No | 1B DiT flow matching, 3000h data, 200+ categories, RLHF. SOTA OSS benchmarks |
| **DeepMotion SayMotion** | $15-300/mo | No | Yes (v2.4) | Inpainting, blending, retarget | Most complete commercial product. The feature bar |
| **Autodesk MotionMaker** | $255/mo (Maya) | No | TBD | Art-directable | Runs locally on CPU. Film/VFX market |
| **Unity AI** (ex-Muse) | Unity sub | No | TBD | Text + video to motion | Biggest long-term threat: native in the engine |

**OSS research models to watch:** MoMask (best FID 0.045), MoSa (2025, autoregressive, FID 0.085), Being-M0 (million-scale MotionLib dataset), MotionGPT (VQ-VAE + LLM).

**Video -> motion (for Core 5, QuickMagic style):** the monocular human-motion-recovery lineage - **GVHMR, TRAM, WHAM**. These recover SMPL motion from a single video. Output `Motion` in HY-Motion's shape and reuse the existing retarget path. QuickMagic itself is the commercial reference (video in, FBX/BVH out, finger tracking).

**HY-Motion's gap vs DeepMotion:** looping, motion editing, inpainting, blending. Looping is table stakes for game animation -> card 11.

## 4. Positioning notes

- **Pipeline company vs model company.** MeshMaker is currently a pipeline/router orchestrating open models. The closest parallel is **VAST-AI/Tripo**: an OSS research lab (TripoSR, TripoSG, UniRig) *and* a commercial platform (Tripo3D) with plugins for 6 editors. That dual model is the long-term template. Pure orchestration has no moat - anyone can assemble the same models - so differentiation eventually needs either fine-tuning or being the standard.
- **The Mixamo playbook (becoming the standard):** be free, be consistent (same skeleton/scale/naming every time), be everywhere (every editor). MeshMaker already outputs Mixamo skeletons - strategically correct. Tripo set the bar with MIT plugins for Blender/Unity/Unreal/ComfyUI/Cocos/Godot.
- **Adoption before revenue:** free hosted tier -> open-source addon + containers -> paid API ("MeshMaker Go") last. The space is pre-market; revenue too early kills dev-tool growth.
- **Cheapest differentiation = animation fine-tuning.** A LoRA on HY-Motion for loopable, snappy, short game-motion clips (LoRA-MDM: few examples, ~12h on a 24GB GPU) would distinguish MeshMaker from stock HY-Motion without training from scratch.

### Revenue benchmarks (for later)

| Platform | Pricing |
|---|---|
| Meshy | $20/mo / 1000 credits |
| Tripo | $16/mo / 3000 credits |
| 3DAI Studio | $14/mo / 1000 credits |

MeshMaker compute cost per full pipeline run (RunPod): ~$0.05-0.15. Healthy margin at any of these price points. Credit-based SaaS is the proven, expected model - don't innovate on pricing, innovate on product.

## Sources

- [Pixal3D](https://github.com/TencentARC/Pixal3D) ([paper](https://arxiv.org/abs/2605.10922)) | [Hunyuan3D 2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | [Hunyuan3D-Omni](https://github.com/Tencent-Hunyuan/Hunyuan3D-Omni)
- [SkinTokens](https://github.com/VAST-AI-Research/SkinTokens) ([paper](https://arxiv.org/abs/2602.04805)) | [UniRig](https://github.com/VAST-AI-Research/UniRig) | [MagicArticulate](https://github.com/Seed3D/MagicArticulate)
- [HY-Motion](https://github.com/Tencent-Hunyuan/HY-Motion-1.0) | [DeepMotion SayMotion](https://www.deepmotion.com/saymotion) | [LoRA-MDM](https://github.com/haimsaw/LoRA-MDM)
- [QuickMagic](https://www.quickmagic.ai/) | [Tripo Blender plugin (MIT)](https://github.com/VAST-AI-Research/tripo-3d-for-blender) | [VAST-AI-Research](https://github.com/VAST-AI-Research)
- [Meshy pricing](https://www.meshy.ai/pricing) | [Tripo pricing](https://www.tripo3d.ai/pricing)
