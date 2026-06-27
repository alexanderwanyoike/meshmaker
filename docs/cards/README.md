# Implementation record

MeshMaker was narrowed to a single capability: **generate a 3D mesh from an
image, via hosted providers.** The numbered cards that planned the journey
(provider abstraction, URL transport, Fal, Meshy, plus the rig/motion/segment
cards) have been retired now that the work shipped or moved out of scope. They
remain in git history on `dev`.

## Shipped

- **Provider spine** - typed `GenerateRequest`, hosted `Asset` URL, registry. See `../ARCHITECTURE.md`.
- **URL asset transport** - download the provider's hosted GLB and import it into Blender.
- **Fal Hunyuan3D 3.1** provider (`fal-ai/hunyuan-3d/v3.1/pro/image-to-3d`).
- **Meshy** image-to-3D provider.

## Next

- More Generate providers as needed. Each is one `Provider` subclass in
  `meshmaker/providers/cloud.py` plus one line in `registry.py` (and an API-key
  preference). See the "Adding a provider" section of `../ARCHITECTURE.md`.
- Generate-side polish: face-count / PBR tuning, retexture, mesh variations.

## Out of scope

Rigging, animation, and part segmentation are separate tools. The old RunPod
containers and Blender tabs for them were removed in the Generate-only cut and
live in git history if ever needed to seed those tools.
