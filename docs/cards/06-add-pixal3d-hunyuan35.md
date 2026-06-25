# Card 06 - Replace Generate with Hunyuan3D 3.5

Status: TODO
Depends on: 01 (provider abstraction), 02 (URL transport)
Quality bar: Meshy-6 meshes

## Goal

Make Hunyuan3D 3.5 the only active Generate backend.

## Why

MeshMaker needs a small, working pipeline more than a router full of experiments.
Trellis2, Hunyuan3D 2.1, Pixal3D, Meshy, and Tripo are out of scope for the first
focused build.

## Scope

- Confirm the real access path for Hunyuan3D 3.5: official open-source weights/container,
  Tencent-hosted API, or another approved endpoint. Do not assume the old Hunyuan3D 2.1
  container can simply be renamed.
- Implement one Generate provider: `Hunyuan3D35`.
- Implement or adapt one handler/client path that returns an `Asset` URL plus metadata
  from day one.
- Remove the Generate backend dropdown unless there is a real second active provider.
- Archive Trellis2 and Hunyuan3D 2.1 from active UI/config after the 3.5 path works.

## Acceptance criteria

- Generate has exactly one active backend in the Blender UI: Hunyuan3D 3.5.
- Generated output imports from an asset URL, not base64.
- Old generator endpoint preferences are no longer required for the main Generate path.

## Notes

As of the June 25, 2026 planning pass, an official open-source Hunyuan3D 3.5 repo/weights
path was not verified. Treat access as the first implementation checkpoint.
