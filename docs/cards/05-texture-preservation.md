# Card 05 - Texture preservation through the rig roundtrip

Status: TODO
Depends on: 02 (URL transport), 03 (rig core)
Quality bar: Meshy-6 meshes (rigged output must not look worse than generated)

## Goal

Keep PBR textures intact through Generate -> Rig -> import. Today rigged characters can come back as grey clay even when the source mesh was textured.

## Why

Trellis2/Hunyuan produce textured GLBs, but the GLB -> MIA -> FBX -> Blender import path drops materials, and the later animation roundtrip degrades them further. Carried over from the old `further-work/004` note.

## Scope

- Audit where textures are lost: MIA FBX export, FBX import material reconstruction, animation export roundtrip.
- Preferred fix: keep textures off the rig path entirely - rig operates on geometry, then re-apply the original generated material to the rigged mesh on the client after import (match by UVs).
- If the FBX must carry textures, ensure the handler packs them and the Blender importer reconnects the PBR nodes.

## Acceptance criteria

- A textured generated mesh, after rigging, retains its PBR material in the Blender viewport.
- Same after a text-to-motion animation pass.

## Notes

Re-applying the source material client-side is usually more robust than fighting FBX material roundtrips.
