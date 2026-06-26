# Card 09 - Meshy provider spike

Status: TODO
Depends on: 01 (provider abstraction), 02 (URL transport)
Quality bar: Meshy-6 meshes

## Goal

Evaluate Meshy as the first external provider for MeshMaker. Start with Generate. Try Rig only as a compatibility spike.

## Why

Meshy has official APIs for Image/Text to 3D, rigging, animation, remesh, retexture, and convert. It may cover more of the pipeline than Fal Hunyuan alone, but rigging must prove skeleton compatibility before it can replace MIA.

## Scope

- Add a Meshy API key preference.
- Implement `MeshyGenerateProvider` for one Image to 3D path.
- Map Meshy responses to `Asset{url, metadata}`.
- Optionally implement a small `MeshyRigProvider` spike against one generated humanoid GLB.
- Inspect the rigged output skeleton in Blender and record whether it has `mixamorig:Hips` or an easy mapping.

## Acceptance criteria

- With a Meshy key configured, the user can generate a textured model and import it identically to the Fal provider.
- Rigging spike has a clear decision: compatible with HY-Motion, mappable, or not usable for the current animation path.

## Notes

Keep this as a spike. Do not add Tripo in the same card.
