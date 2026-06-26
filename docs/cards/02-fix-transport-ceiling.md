# Card 02 - Provider-agnostic URL asset transport

Status: TODO
Depends on: 01 (asset-as-URL types)
Quality bar: Meshy-6 meshes (this is the prerequisite for it)

## Goal

Make the Blender client import assets from URLs as well as legacy inline bytes. Hosted providers such as Fal and Meshy already return file URLs; RunPod handlers can be migrated later if we keep them.

## Why

The old RunPod path returns GLB/FBX data as base64 inside JSON, which hits response-size limits and forces quality compromises. Fal/Meshy avoid this by returning hosted asset URLs. The client should consume the standard `Asset{url, metadata}` contract regardless of provider.

## Scope

- Add a stdlib-only download helper in `meshmaker/api.py` that downloads an asset URL to a temp file.
- Update operator import paths to use `Asset.url` when present and `Asset.data` only for legacy providers.
- Keep legacy RunPod base64 support isolated in `meshmaker/providers/runpod.py`.
- Do not provision R2 unless we choose to keep custom RunPod handlers that need it.
- Add tests for URL asset download and provider URL mapping.

## Acceptance criteria

- Client import path works from a hosted/presigned URL.
- Existing legacy RunPod providers still work through inline bytes.
- Card 06 can implement Fal Hunyuan3D without touching Blender import logic.

## Notes

This unblocks hosted Generate providers first. R2 remains an option only for custom RunPod handlers.
