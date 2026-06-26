# MeshMaker - Architecture

> The "how" behind `VISION.md`. Read VISION first for the what/why.

## The one organizing idea: capability -> provider

The project's spine is a small abstraction. Stop organizing UI code **by model** (a Trellis handler, a Hunyuan handler, a MIA handler, each with bespoke operators). Organize it **by capability**, with one focused provider per capability for the current slice.

- A **capability** is one of the 5 cores: Generate, Segment, Rig, Motion, VideoMotion.
- A **provider** is a concrete backend that fulfils a capability: `FalHunyuan3D`, `MeshyGenerate`, `RunPodMIA`, `RunPodHYMotion`, etc.
- A provider **declares which capabilities it supports** and how to invoke them. For now, Generate starts with Fal Hunyuan3D. Meshy is the first external-provider spike.

This is what keeps MeshMaker from becoming a pile of scripts. Every new idea becomes obvious to place: it is a new **capability**, a replacement **provider**, or a **UI/addon** change. Nothing floats.

### The provider interface (target)

A small base class. Every provider implements the capabilities it claims.

```python
class Provider:
    name: str
    capabilities: set[Capability]   # {Capability.GENERATE, ...}

    def supports(self, cap: Capability) -> bool: ...

    # Each capability has one method with a stable signature.
    # Providers implement only the ones they declare.
    def generate(self, req: GenerateRequest) -> Asset: ...      # image -> mesh
    def segment(self, req: SegmentRequest) -> list[Asset]: ...  # mesh -> parts
    def rig(self, req: RigRequest) -> Asset: ...                # mesh -> rigged
    def motion(self, req: MotionRequest) -> Motion: ...         # text -> motion
    def video_motion(self, req: VideoRequest) -> Motion: ...    # video -> motion
```

Requests carry capability-specific quality knobs (resolution, steps, guidance, octree, etc.). `Asset` is always a URL + metadata (see transport rule below), never raw base64.

## Target repo layout (5 cores, self-contained)

Each core is a vertical slice: Blender UI + provider bindings on the client, and one container per RunPod-hosted model. You should be able to open one core and work without touching the others.

```
meshmaker/                     # Blender addon (the client)
  __init__.py                  # entry point, tab registration
  api.py                       # HTTP transport and asset download helpers (stdlib only)
  preferences.py               # active endpoint IDs + keys + storage config
  providers/                   # NEW: the provider abstraction
    base.py                    #   Provider, Capability, request/response types
    runpod.py                  #   RunPod-backed providers (one per container)
    cloud.py                   #   Fal/Meshy hosted providers
    registry.py                #   discovery: which providers support what
  core/
    generate/                  # Core 1: image -> mesh    (was mesh/)
    segment/                   # Core 2: mesh -> parts     (was segment/)
    rig/                       # Core 3: mesh -> rigged
    motion/                    # Core 4: text -> motion    (was anim/)
    video/                     # Core 5: video -> animation (NEW, stub first)
  retarget/                    # shared: motion -> rigged character (used by 4 and 5)

containers/                    # RunPod serverless handlers (the backends)
  trellis2/      hunyuan3d/    # Legacy Generate references, not active targets
  hunyuan3d-part/              # Segment
  mia/  skintokens/            # Rig (skintokens NEW)
  hymotion/                    # Motion (+ retarget_fbx.py, shared)
  video-mocap/                 # VideoMotion (NEW)
```

Naming: the current addon uses `mesh/`, `anim/` tab names. Target renames them to the core names (`generate/`, `motion/`) so the code matches VISION's vocabulary. Card 03 covers the restructure.

## Data flow

```
Blender (core UI)
  -> build a typed Request with quality knobs
  -> Provider.<capability>(req)        # registry picks the single active backend
       Hosted provider: call Fal/Meshy REST -> their asset URL
       RunPod provider: legacy MIA/HY-Motion/segment path, inline bytes until migrated
  -> Asset{ url, metadata }            # always a URL, never base64
  -> client downloads from url, imports into the scene
```

### The transport rule

**New providers should return asset URLs, not raw base64 GLB/FBX in JSON.** Fal and Meshy already fit this shape. Legacy RunPod providers may keep inline bytes until they are migrated or removed. The Blender import path must accept `Asset.url` first and `Asset.data` only as a compatibility fallback.

## How the two motion cores share one path

Core 4 (Text -> Motion) and Core 5 (Video -> Animation) are different **front ends to the same back half**. Both produce a `Motion` (SMPL-H style joint data). Both feed the existing retarget step (`containers/hymotion/retarget_fbx.py`, a 700+ entry SMPL-H -> Mixamo bone mapping) to apply the motion onto a rigged character. So Core 5 is mostly: add a monocular human-motion-recovery container (GVHMR / TRAM / WHAM lineage), output `Motion` in the same shape HY-Motion uses, and reuse the retarget path unchanged.

## Backend swap rules (so quality upgrades stay contained)

- **Rig backends must output a Mixamo-compatible skeleton** (`mixamorig:Hips` hierarchy). This is why MIA was chosen over UniRig: HY-Motion's retargeting expects Mixamo bone names. When swapping MIA -> SkinTokens, verify its skeleton maps into that retarget path, or add a mapping. (See REFERENCE for the MIA/UniRig/SkinTokens detail.)
- **Generate must return a URL to a GLB/OBJ bundle** with PBR textures. For the focused build, this means Fal Hunyuan3D first.
- **Meshy is the first external provider spike.** Start with Generate. Rigging is allowed only after checking whether the output skeleton has `mixamorig:Hips` or an easy mapping.

## Quality bars, made concrete

- **Generate:** Fal Hunyuan3D + URL assets first. Meshy is the comparison/spike provider once the Fal path works.
- **Motion (Cascadeur-grade):** a clean Mixamo FBX with no catastrophic foot-sliding is enough; the human polishes in Cascadeur/Blender. Looping (card 11) and foot-contact cleanup raise it further.
