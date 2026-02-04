# CharMaker - Vision Document

## The Pivot

**Old scope:** Motion Creator - text-to-animation via HY-Motion
**New scope:** CharMaker - end-to-end game character pipeline

---

## The Pipeline

```
Text/Image → 3D Model → Rigged Character → Animated Character → Game-Ready
    ↓            ↓              ↓                  ↓                 ↓
 Prompt     Trellis 2       UniRig           HY-Motion           FBX/GLB
            Hunyuan 3D       (GLB→FBX)        (text→motion)
```

---

## Research Findings

### Stage 1: 3D Model Generation

#### Trellis 2 (Microsoft)
[GitHub](https://github.com/microsoft/TRELLIS.2) | [Demo](https://microsoft.github.io/TRELLIS.2/)

| Spec | Value |
|------|-------|
| Parameters | 4B |
| Input | Image or text |
| Output | **GLB** (PBR), OBJ, PLY |
| Texture | Up to 4096×4096 |
| Speed | 3-17s on H100 |
| Topology | Handles complex/open/non-manifold |
| Engine Support | Unity, Unreal, Blender |

#### Hunyuan 3D 2.1 (Tencent)
[GitHub](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) | [Demo](https://hunyuan-3d.org/)

| Spec | Value |
|------|-------|
| Input | Image or text |
| Output | **GLB**, OBJ |
| Topology | "Smart Topology" - clean quad/tri mesh |
| Pipeline | Shape gen → Texture synthesis (decoupled) |
| Engine Support | Unity, Unreal, Blender |

**Verdict:** Both output GLB. Trellis 2 is faster, Hunyuan has cleaner topology option.

---

### Stage 2: Auto-Rigging

#### UniRig (VAST-AI)
[GitHub](https://github.com/VAST-AI-Research/UniRig) | [Paper](https://dl.acm.org/doi/10.1145/3730930)

| Spec | Value |
|------|-------|
| Input | **.obj, .fbx, .glb, .vrm** |
| Output | **FBX** (skeleton + skinning) |
| Skeleton | **Mixamo-compatible** (`<mixamo:body>` tokens) |
| VRAM | 8GB minimum |
| Training Data | Mixamo, VRoid, Rig-XL |

**Key finding:** UniRig was trained on Mixamo data and outputs Mixamo-compatible skeletons. This is exactly what we need.

---

### Stage 3: Animation

#### HY-Motion (Tencent)
[GitHub](https://github.com/Tencent-Hunyuan/HY-Motion-1.0) | We already have this

| Spec | Value |
|------|-------|
| Input | Text prompt |
| Output | SMPL-H (.npz) |
| VRAM | ~26GB (48GB GPU recommended) |
| Limitations | No looping support |

**Retargeting solved:**
- [hy-motion-fbx-exporter](https://github.com/zysilm-ai/hy-motion-fbx-exporter) - CLI, Mixamo FBX output
- [ComfyUI-HY-Motion1](https://github.com/jtydhr88/ComfyUI-HY-Motion1) - GLB/FBX export with Mixamo retarget

Both take a Mixamo-rigged FBX as input and output animation on that skeleton.

---

### Stage 4: Desktop App

#### Tauri 2.0
[Docs](https://v2.tauri.app/)

| Spec | Value |
|------|-------|
| Frontend | **React + TypeScript** ✓ |
| Backend | Rust (minimal needed) |
| Bundle Size | ~3MB vs Electron's 150MB+ |
| Platforms | Windows, macOS, Linux |

**Good fit:** User knows React/TypeScript. Rust is mainly for:
- File system access
- Calling RunPod APIs
- Optional: local inference via Python subprocess

---

## Format Compatibility Matrix

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Trellis 2  │     │   UniRig    │     │  HY-Motion  │     │   Export    │
│  Hunyuan 3D │     │             │     │             │     │             │
├─────────────┤     ├─────────────┤     ├─────────────┤     ├─────────────┤
│ OUT: GLB    │────▶│ IN: GLB     │     │ IN: text    │     │ IN: NPZ+FBX │
│      OBJ    │     │ OUT: FBX    │────▶│ OUT: NPZ    │────▶│ OUT: FBX    │
│             │     │ (Mixamo)    │     │ (SMPL-H)    │     │      GLB    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

**All formats chain together.**

---

## Architecture

### Monorepo Structure

```
charmaker/
├── app/                    # Tauri desktop app
│   ├── src/                # React frontend
│   ├── src-tauri/          # Rust backend
│   └── package.json
├── containers/
│   ├── trellis2/           # 3D generation
│   │   ├── Dockerfile
│   │   └── handler.py
│   ├── unirig/             # Auto-rigging
│   │   ├── Dockerfile
│   │   └── handler.py
│   └── hymotion/           # Animation (existing)
│       ├── Dockerfile
│       └── handler.py
├── shared/
│   ├── types/              # Shared TypeScript types
│   └── python/             # Shared Python utils
└── README.md
```

### RunPod Containers

| Container | GPU | VRAM | Cold Start |
|-----------|-----|------|------------|
| Trellis 2 | A100/H100 | 40GB+ | ~30s |
| UniRig | RTX 4090/A6000 | 8GB+ | ~20s |
| HY-Motion | A100/A6000 | 48GB | ~30s |

---

## Reference: PixelArtistry ComfyUI Workflow

[Source](https://pixel-artistry.com/ComfyRigAnimate)

They've already built this pipeline in ComfyUI:
- HyMotion integration
- Make-It-Animatable (MIA)
- Custom workflow files (Google Drive)

**Action:** Download and analyze their workflow for reference.

---

## Gaps to Address

### Technical
- [x] ~~SMPL-H → Mixamo retargeting~~ - solved by hy-motion-fbx-exporter
- [ ] Animation looping (see looping-technical-card.md) - **defer, models will improve**
- [ ] Batch processing UI

### Research
- [ ] Trellis 2 vs Hunyuan 3D quality comparison
- [ ] UniRig failure cases (what meshes don't rig well?)
- [ ] PixelArtistry workflow analysis

### Tauri App
- [ ] Basic shell with 4-stage pipeline
- [ ] RunPod API integration
- [ ] File management (GLB → FBX → NPZ → final)
- [ ] 3D preview (Three.js?)

---

## MVP Scope

**Phase 1: Prove the pipeline**
1. Get all 3 containers running on RunPod
2. Manual CLI workflow: image → GLB → rigged FBX → animated FBX
3. Validate output imports into Unity/Godot/Unreal

**Phase 2: Basic Tauri app**
1. Simple wizard UI (4 steps)
2. Upload image → get animated character
3. Download final FBX

**Phase 3: Polish**
1. Animation looping
2. Multiple animation generation
3. Local preview
4. Batch processing

---

## Open Questions

1. **Trellis 2 licensing?** - MIT? Can we use commercially?
2. **UniRig licensing?** - Apache 2.0 (confirmed)
3. **Hunyuan 3D licensing?** - Need to check
4. **Do we need all 3 on RunPod?** - UniRig might run locally (8GB VRAM)

---

## Next Steps

1. [ ] Analyze PixelArtistry workflow
2. [ ] Create Trellis 2 RunPod container
3. [ ] Create UniRig RunPod container
4. [ ] Test full pipeline manually
5. [ ] Scaffold Tauri app
