# MeshMaker - Vision

> The single source of truth. If you're coming back to this project and feel lost, read this file first. Companion docs: `ARCHITECTURE.md` (the how), `REFERENCE.md` (model/competitor landscape), `cards/` (the implementation plan).

## What MeshMaker is

**An open frontend for 3D character creation, living inside Blender.** You pick a capability (generate, rig, animate...), MeshMaker sends the job to one focused backend for that capability, and the result lands cleanly in your scene. Keep the first build small: one hosted high-quality Generate path, then only the rig/motion work needed to make that output useful.

"MeshMaker Go" - a hosted, always-warm version we operate - is a future *provider*, added last, once the open tool has users who feel the pain of running their own GPUs.

## The two quality bars (the north star)

Every decision serves these two:

1. **Meshes must look very high quality** - production-usable, not clay. For the focused build, the first active Generate target is Fal Hunyuan3D v3/v3.1, with Meshy as the first external provider spike.
2. **Animations must be Cascadeur-grade starting points** - not final, but a clean enough skeleton/motion that a human refines in Cascadeur or Blender. No catastrophic foot-sliding. This bar is achievable today with HY-Motion -> Mixamo FBX.

## Architecture: 5 cores + addons

Two layers. The five cores are the whole project. Everything else is a topping.

### The 5 dedicated cores

Each core is self-contained: its own Blender tab, its own swappable backend(s), independently testable. You should be able to fix one without touching the others.

| # | Core | In -> Out | Code (today) | Backend now | Backend target |
|---|------|-----------|--------------|-------------|----------------|
| 1 | **Generate** | image -> mesh | `meshmaker/mesh/` + legacy `containers/trellis2`, `containers/hunyuan3d` | legacy RunPod Trellis2/Hunyuan3D 2.1 | Fal Hunyuan3D v3/v3.1 first; Meshy spike next |
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

1. **The 20MB base64 transport ceiling.** Legacy RunPod handlers return GLB/FBX data as base64 inside JSON; RunPod's sync limit is ~20MB. Hosted providers such as Fal and Meshy return asset URLs. **Fix: make the client import URL assets and keep inline bytes only as a legacy provider path.**
2. **Hosted provider choice.** The old Trellis2/Hunyuan3D 2.1 containers are no longer the Generate target. Start with Fal Hunyuan3D v3/v3.1. Evaluate Meshy next because it can cover Generate, Rig, Animation, Remesh, Retexture, and Convert.
3. **Texture loss in the rig roundtrip** (further-work/004). Rigged output looks worse than generated output until fixed.

## Roadmap (anchored on the quality bars)

See `cards/` for the numbered, ordered implementation plan. In brief:

**Now - smallest useful pipeline**
- Provider abstraction as a thin spine (card 01)
- Add provider-agnostic URL asset transport (card 02)
- Add Fal Hunyuan3D as the first hosted Generate provider (card 06)
- Spike Meshy as the first broader external provider (card 09)
- Fix texture preservation only if the rig roundtrip damages the chosen output (card 05)

**Deferred**
- Five-core restructure, old generator quality-default tuning, Pixal3D, Tripo, SkinTokens, segment tuning, video-to-animation, looping, and addons.

## Reference

- `ARCHITECTURE.md` - the technical spec: provider model, target repo layout, per-core design, data flow
- `REFERENCE.md` - distilled model/competitor landscape (mesh, rig, animation) + positioning/revenue notes
- `cards/` - the implementation plan (cores first, then addons)

## Naming note

This project was called CharMaker and Motion Creator in earlier docs. **The name is MeshMaker.** Those superseded docs were removed in the `docs/finalize-architecture` reset; git history on `dev` retains them if ever needed.
