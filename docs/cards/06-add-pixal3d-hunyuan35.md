# Card 06 - Add Fal Hunyuan3D Generate provider

Status: TODO
Depends on: 01 (provider abstraction), 02 (URL transport)
Quality bar: Meshy-6 meshes

## Goal

Make Fal's hosted Hunyuan3D v3/v3.1 API the first active Generate backend.

## Why

MeshMaker needs a small, working pipeline more than a router full of experiments.
Fal removes the custom RunPod container, model-cache, network-volume, and base64-response problems from Generate. It returns hosted model URLs that fit the provider `Asset` contract directly.

## Scope

- Add a Fal API key preference.
- Implement one Generate provider for Fal Hunyuan3D v3/v3.1 image-to-3D.
- Implement or adapt one handler/client path that returns an `Asset` URL plus metadata
  from day one.
- Remove the old RunPod Generate backends from the active UI after the Fal path works.
- Keep Trellis2 and Hunyuan3D 2.1 code as legacy reference until we are confident the hosted path is enough.

## Acceptance criteria

- Generate has exactly one active backend in the Blender UI: Fal Hunyuan3D.
- Generated output imports from an asset URL, not base64.
- Old generator endpoint preferences are no longer required for the main Generate path.

## Notes

Current candidate endpoints: `fal-ai/hunyuan3d-v3/image-to-3d` or Fal Hunyuan 3D Pro v3.1. Pick the one that gives the best Blender-ready GLB/OBJ output for the cost.
