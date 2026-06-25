# MeshMaker - Vision

> The single source of truth. If you're coming back to this project and feel lost, read this file first. Companion docs: `ARCHITECTURE.md` (the how), `REFERENCE.md` (model/competitor landscape), `cards/` (the implementation plan).

## What MeshMaker is

**An open frontend for 3D character creation, living inside Blender.** You pick a capability (generate, rig, animate...), MeshMaker sends the job to one focused backend for that capability, and the result lands cleanly in your scene. Keep the first build small: one high-quality Generate path, then only the rig/motion work needed to make that output useful.

"MeshMaker Go" - a hosted, always-warm version we operate - is a future *provider*, added last, once the open tool has users who feel the pain of running their own GPUs.

## The two quality bars (the north star)

Every decision serves these two:

1. **Meshes must look very high quality** - production-usable, not clay. For the focused build, the only active Generate target is Hunyuan3D 3.5, after the transport ceiling is fixed (see Known Blockers).
2. **Animations must be Cascadeur-grade starting points** - not final, but a clean enough skeleton/motion that a human refines in Cascadeur or Blender. No catastrophic foot-sliding. This bar is achievable today with HY-Motion -> Mixamo FBX.

## Architecture: 5 cores + addons

Two layers. The five cores are the whole project. Everything else is a topping.

### The 5 dedicated cores

Each core is self-contained: its own Blender tab, its own swappable backend(s), independently testable. You should be able to fix one without touching the others.

| # | Core | In -> Out | Code (today) | Backend now | Backend target |
|---|------|-----------|--------------|-------------|----------------|
| 1 | **Generate** | image -> mesh | `meshmaker/mesh/` + legacy `containers/trellis2`, `containers/hunyuan3d` | legacy Trellis2/Hunyuan3D 2.1 | Hunyuan3D 3.5 only |
| 2 | **Segment** | mesh -> parts | `meshmaker/segment/` + `containers/hunyuan3d-part` | P3-SAM | P3-SAM with exposed tuning knobs |
| 3 | **Rig** | mesh -> rigged | `meshmaker/rig/` + `containers/mia` | MIA | SkinTokens / TokenRig |
| 4 | **Text -> Motion** | text -> motion clip | `meshmaker/anim/` + `containers/hymotion` | HY-Motion | HY-Motion (+ looping addon) |
| 5 | **Video -> Animation** | video -> motion (QuickMagic style) | NOT BUILT | none | new container: GVHMR / TRAM / WHAM lineage |

Cores 4 and 5 both produce motion that flows through the **same retarget-onto-character step** (already written for HY-Motion in `containers/hymotion`, `retarget_fbx.py`). Building core 5 is mostly "add a monocular mocap container" and reuse that path.

### The addons layer

Addons are features built *on top of* a solid core. None of these are the project; they are toppings added once the cores work and hit the quality bars. They live in the backlog half of `cards/`.

- **On Generate:** retexturing, texture upscaling, mesh variations, mesh editing, props/environments, batch generation
- **On Motion:** looping (card 11), animation library
- **On Animate:** game-engine export
- **Cross-cutting:** clean mesh output / naming, test harness

## Known blockers (read before chasing model quality)

1. **The 20MB base64 transport ceiling.** Handlers return the GLB as base64 inside the JSON response; RunPod's sync limit is ~20MB. This forces `texture_size=1024` and aggressive decimation regardless of model. **Fix: write outputs to object storage (S3/R2) and return a URL.** This single change is the prerequisite for hitting bar #1. It is the highest-leverage task in the whole project.
2. **Hunyuan3D 3.5 access path.** The old Trellis2/Hunyuan3D 2.1 containers are no longer the Generate target. First confirm whether 3.5 is available as official open-source weights/container, a Tencent-hosted API, or another approved endpoint.
3. **Texture loss in the rig roundtrip** (further-work/004). Rigged output looks worse than generated output until fixed.

## Roadmap (anchored on the quality bars)

See `cards/` for the numbered, ordered implementation plan. In brief:

**Now - smallest useful pipeline**
- Provider abstraction as a thin spine (card 01)
- Fix the transport ceiling with R2/object-storage URLs (card 02)
- Replace Generate with Hunyuan3D 3.5 only (card 06)
- Fix texture preservation only if the rig roundtrip damages the chosen output (card 05)

**Deferred**
- Five-core restructure, old generator quality-default tuning, Pixal3D, Meshy/Tripo, SkinTokens, segment tuning, video-to-animation, looping, and addons.

## Reference

- `ARCHITECTURE.md` - the technical spec: provider model, target repo layout, per-core design, data flow
- `REFERENCE.md` - distilled model/competitor landscape (mesh, rig, animation) + positioning/revenue notes
- `cards/` - the implementation plan (cores first, then addons)

## Naming note

This project was called CharMaker and Motion Creator in earlier docs. **The name is MeshMaker.** Those superseded docs were removed in the `docs/finalize-architecture` reset; git history on `dev` retains them if ever needed.
