# MeshMaker - Architecture

> The "how" behind `VISION.md`. Read VISION first for the what/why.

## The one organizing idea: capability -> provider

The project's spine is a single abstraction. Stop organizing code **by model** (a Trellis handler, a Hunyuan handler, a MIA handler, each with bespoke operators). Organize it **by capability, with a swappable provider behind each.**

- A **capability** is one of the 5 cores: Generate, Segment, Rig, Motion, VideoMotion.
- A **provider** is a concrete backend that fulfils a capability: `RunPodTrellis`, `RunPodHunyuan`, `Pixal3D`, `MeshyCloud`, `TripoCloud`, `RunPodMIA`, `RunPodSkinTokens`, etc.
- A provider **declares which capabilities it supports** and how to invoke them. The Blender UI asks "who can Generate?" and shows the user a dropdown.

This is what makes MeshMaker a router rather than a pile of scripts. Every new idea becomes obvious to place: it's a new **capability**, a new **provider**, or a **UI/addon** change. Nothing floats.

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
  api.py                       # RunPod + storage transport (stdlib only)
  preferences.py               # endpoint IDs + keys + storage config
  providers/                   # NEW: the provider abstraction
    base.py                    #   Provider, Capability, request/response types
    runpod.py                  #   RunPod-backed providers (one per container)
    cloud.py                   #   external providers (Meshy, Tripo)
    registry.py                #   discovery: which providers support what
  core/
    generate/                  # Core 1: image -> mesh    (was mesh/)
    segment/                   # Core 2: mesh -> parts     (was segment/)
    rig/                       # Core 3: mesh -> rigged
    motion/                    # Core 4: text -> motion    (was anim/)
    video/                     # Core 5: video -> animation (NEW, stub first)
  retarget/                    # shared: motion -> rigged character (used by 4 and 5)

containers/                    # RunPod serverless handlers (the backends)
  trellis2/      hunyuan3d/    # Generate
  pixal3d/                     #   (NEW)
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
  -> Provider.<capability>(req)        # registry picks the backend the user chose
       RunPod provider:  POST /run -> poll /status -> backend writes output to object storage
       Cloud provider:   call Meshy/Tripo REST -> their URL
  -> Asset{ url, metadata }            # always a URL, never base64
  -> client downloads from url, imports into the scene
```

### The transport rule (this is load-bearing)

**Handlers must write their output to object storage (S3 / Cloudflare R2) and return a URL. Never return raw base64 GLB/FBX in the JSON response.** RunPod's synchronous response caps around 20MB; base64 inflates bytes ~33%. Returning assets inline is what forced `texture_size=1024` and aggressive decimation across every model regardless of its true quality. This rule is the single prerequisite for the "Meshy 6 quality" bar. See blocker #1 in VISION and card 02.

## How the two motion cores share one path

Core 4 (Text -> Motion) and Core 5 (Video -> Animation) are different **front ends to the same back half**. Both produce a `Motion` (SMPL-H style joint data). Both feed the existing retarget step (`containers/hymotion/retarget_fbx.py`, a 700+ entry SMPL-H -> Mixamo bone mapping) to apply the motion onto a rigged character. So Core 5 is mostly: add a monocular human-motion-recovery container (GVHMR / TRAM / WHAM lineage), output `Motion` in the same shape HY-Motion uses, and reuse the retarget path unchanged.

## Backend swap rules (so quality upgrades stay contained)

- **Rig backends must output a Mixamo-compatible skeleton** (`mixamorig:Hips` hierarchy). This is why MIA was chosen over UniRig: HY-Motion's retargeting expects Mixamo bone names. When swapping MIA -> SkinTokens, verify its skeleton maps into that retarget path, or add a mapping. (See REFERENCE for the MIA/UniRig/SkinTokens detail.)
- **Generate backends must return a URL to a GLB** with PBR textures. Geometry/topology and texture resolution are the differentiators; the contract is the same.
- **External cloud providers (Meshy/Tripo)** are just providers that call someone else's REST API and return their URL. They're the fallback when self-hosted output can't hit the quality bar.

## Quality bars, made concrete

- **Generate (Meshy 6 tier):** newest models (Pixal3D / Hunyuan3D 3.5) + the transport rule + full settings (resolution >= 1024, texture_size up to 4096). A/B self-hosted vs Meshy/Tripo per input; route to the winner.
- **Motion (Cascadeur-grade):** a clean Mixamo FBX with no catastrophic foot-sliding is enough; the human polishes in Cascadeur/Blender. Looping (card 11) and foot-contact cleanup raise it further.
